// atlas-validate checks a raw game capture against a local profile.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"

	"github.com/google/jsonschema-go/jsonschema"
)

type collection struct {
	Name, Path, IDField, Schema string
}

type referenceRule struct {
	Models          []string
	Field, Target   string
	ExternalSymbols map[string]string
	Aliases         map[string]string
}

type profile struct {
	FormatVersion    int
	Game, SchemaFile string
	RequiredFiles    []string
	Collections      []collection
	ModelSchemas     map[string]string
	References       []referenceRule
	Reading          json.RawMessage
}

type diagnostic struct {
	File    string `json:"file"`
	Pointer string `json:"pointer"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

type report struct {
	Valid              bool                  `json:"valid"`
	Game               string                `json:"game,omitempty"`
	GameVersion        string                `json:"gameVersion,omitempty"`
	FilesChecked       int                   `json:"filesChecked"`
	ReferencesChecked  int                   `json:"referencesChecked"`
	ExternalReferences int                   `json:"externalReferences"`
	Errors             []diagnostic          `json:"errors"`
	Relations          []relation            `json:"relations,omitempty"`
	Backlinks          map[string][]location `json:"backlinks,omitempty"`
}

type location struct {
	File    string `json:"file"`
	Pointer string `json:"pointer"`
}

type relation struct {
	File             string   `json:"file"`
	Pointer          string   `json:"pointer"`
	Value            string   `json:"value"`
	TargetCollection string   `json:"targetCollection"`
	TargetID         string   `json:"targetId"`
	TargetFiles      []string `json:"targetFiles"`
	External         bool     `json:"external,omitempty"`
}

type pendingReference struct {
	File, Pointer, Value string
	Rule                 referenceRule
}

func (r *report) add(file, pointer, code, message string) {
	r.Errors = append(r.Errors, diagnostic{file, pointer, code, message})
}

// Decode tokens so duplicate keys are errors, rather than silently taking the last value.
func decodeJSON(raw []byte) (any, error) {
	d := json.NewDecoder(bytes.NewReader(raw))
	var read func() (any, error)
	read = func() (any, error) {
		token, err := d.Token()
		if err != nil {
			return nil, err
		}
		switch token {
		case json.Delim('{'):
			object := map[string]any{}
			for d.More() {
				keyToken, err := d.Token()
				if err != nil {
					return nil, err
				}
				key := keyToken.(string)
				if _, exists := object[key]; exists {
					return nil, fmt.Errorf("duplicate JSON key %q at byte %d", key, d.InputOffset())
				}
				value, err := read()
				if err != nil {
					return nil, err
				}
				object[key] = value
			}
			_, err := d.Token()
			return object, err
		case json.Delim('['):
			array := []any{}
			for d.More() {
				value, err := read()
				if err != nil {
					return nil, err
				}
				array = append(array, value)
			}
			_, err := d.Token()
			return array, err
		default:
			return token, nil
		}
	}
	value, err := read()
	if err != nil {
		return nil, err
	}
	if _, err := d.Token(); err != io.EOF {
		if err == nil {
			err = fmt.Errorf("extra JSON value at byte %d", d.InputOffset())
		}
		return nil, err
	}
	return value, nil
}

func readJSON(path string) (any, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return decodeJSON(raw)
}

func typeName(value string) string {
	value = strings.SplitN(value, "[", 2)[0]
	value = strings.SplitN(value, ",", 2)[0]
	return value[strings.LastIndex(value, ".")+1:]
}

func pointerToken(value string) string {
	return strings.ReplaceAll(strings.ReplaceAll(value, "~", "~0"), "/", "~1")
}

func localPath(root, relative string) (string, error) {
	if !filepath.IsLocal(filepath.FromSlash(relative)) {
		return "", fmt.Errorf("expected a local relative path, got %q", relative)
	}
	return filepath.Join(root, filepath.FromSlash(relative)), nil
}

func loadProfile(directory string) (profile, map[string]*jsonschema.Resolved, error) {
	var p profile
	value, err := readJSON(filepath.Join(directory, "game-profile.json"))
	if err != nil {
		return p, nil, err
	}
	raw, _ := json.Marshal(value)
	if err = json.Unmarshal(raw, &p); err != nil {
		return p, nil, err
	}
	schemaPath, err := localPath(directory, p.SchemaFile)
	if err != nil {
		return p, nil, err
	}
	schemaValue, err := readJSON(schemaPath)
	if err != nil {
		return p, nil, err
	}
	raw, _ = json.Marshal(schemaValue)
	var schema jsonschema.Schema
	if err = json.Unmarshal(raw, &schema); err != nil {
		return p, nil, err
	}
	schemas := map[string]*jsonschema.Resolved{}
	for name := range schema.Defs {
		wrapper := &jsonschema.Schema{Schema: schema.Schema, Defs: schema.Defs, Ref: "#/$defs/" + pointerToken(name)}
		resolved, err := wrapper.Resolve(nil) // Remote schema loading is disabled.
		if err != nil {
			return p, nil, fmt.Errorf("schema %s: %w", name, err)
		}
		schemas[name] = resolved
	}
	if schemas["profile"] == nil {
		return p, nil, fmt.Errorf("schema is missing definition %q", "profile")
	}
	if err := schemas["profile"].Validate(value); err != nil {
		return p, nil, fmt.Errorf("game-profile.json: %w", err)
	}
	if p.FormatVersion != 1 {
		return p, nil, fmt.Errorf("unsupported profile version %d", p.FormatVersion)
	}
	names := map[string]bool{}
	for _, collection := range p.Collections {
		if names[collection.Name] {
			return p, nil, fmt.Errorf("duplicate collection %q", collection.Name)
		}
		names[collection.Name] = true
		if _, err := localPath(".", collection.Path); err != nil {
			return p, nil, err
		}
		if schemas[collection.Schema] == nil {
			return p, nil, fmt.Errorf("unknown schema %q", collection.Schema)
		}
		if strings.HasPrefix(collection.IDField, "@") && collection.IDField != "@keys" && collection.IDField != "@parent" && collection.IDField != "@stem" && collection.IDField != "@path" {
			return p, nil, fmt.Errorf("unknown identity selector %q", collection.IDField)
		}
	}
	for model, schema := range p.ModelSchemas {
		if schemas[schema] == nil {
			return p, nil, fmt.Errorf("model %s uses unknown schema %q", model, schema)
		}
	}
	for _, rule := range p.References {
		if !names[rule.Target] {
			return p, nil, fmt.Errorf("unknown reference target %q", rule.Target)
		}
		for symbol, reason := range rule.ExternalSymbols {
			if symbol == "" || reason == "" {
				return p, nil, fmt.Errorf("external symbols require a value and reason")
			}
		}
	}
	for _, path := range p.RequiredFiles {
		if _, err := localPath(".", path); err != nil {
			return p, nil, err
		}
	}
	return p, schemas, nil
}

func matches(path, collectionPath string) bool {
	return path == collectionPath || strings.HasPrefix(path, collectionPath+"/")
}

func validate(dataDirectory, profileDirectory string, includeRelations bool) (report, int) {
	r := report{Errors: []diagnostic{}}
	p, schemas, err := loadProfile(profileDirectory)
	if err != nil {
		r.add("game-profile.json", "", "profile", err.Error())
		return r, 2
	}
	r.Game = p.Game
	info, err := os.Stat(dataDirectory)
	if err != nil || !info.IsDir() {
		r.add(dataDirectory, "", "data_directory", "data path must be an existing directory")
		return r, 2
	}
	var paths []string
	err = filepath.WalkDir(dataDirectory, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !entry.IsDir() && strings.HasSuffix(entry.Name(), ".json") {
			relative, _ := filepath.Rel(dataDirectory, path)
			paths = append(paths, filepath.ToSlash(relative))
		}
		return nil
	})
	if err != nil {
		r.add(dataDirectory, "", "read", err.Error())
		return r, 1
	}
	sort.Strings(paths)
	files := map[string]bool{}
	for _, path := range paths {
		files[path] = true
	}
	for _, path := range p.RequiredFiles {
		if !files[path] {
			r.add(path, "", "missing_file", "file required by the profile is missing")
		}
	}
	indices := map[string]map[string][]string{}
	for _, collection := range p.Collections {
		indices[collection.Name] = map[string][]string{}
	}
	rulesByModel := map[string][]referenceRule{}
	for _, rule := range p.References {
		for _, model := range rule.Models {
			rulesByModel[model] = append(rulesByModel[model], rule)
		}
	}
	var pending []pendingReference
	for _, path := range paths {
		value, err := readJSON(filepath.Join(dataDirectory, filepath.FromSlash(path)))
		r.FilesChecked++
		if err != nil {
			r.add(path, "", "json", err.Error())
			continue
		}
		object, ok := value.(map[string]any)
		if !ok {
			r.add(path, "", "schema", "capture files must contain a JSON object")
			continue
		}
		checked := map[string]bool{}
		for _, collection := range p.Collections {
			if !matches(path, collection.Path) {
				continue
			}
			if !checked[collection.Schema] {
				if err := schemas[collection.Schema].Validate(object); err != nil {
					r.add(path, "", "schema", err.Error())
				}
				checked[collection.Schema] = true
			}
			var ids []string
			switch collection.IDField {
			case "@keys":
				for key := range object {
					if !strings.HasPrefix(key, "$") {
						ids = append(ids, key)
					}
				}
			case "@parent":
				ids = []string{filepath.Base(filepath.Dir(path))}
			case "@stem":
				ids = []string{strings.TrimSuffix(filepath.Base(path), ".json")}
			case "@path":
				ids = []string{strings.TrimPrefix(path, collection.Path+"/")}
			default:
				id, _ := object[collection.IDField].(string)
				if id == "" {
					r.add(path, "/"+pointerToken(collection.IDField), "identity", "record identity must be a nonempty string")
				} else {
					ids = []string{id}
				}
			}
			for _, id := range ids {
				if prior, exists := indices[collection.Name][id]; exists && collection.IDField != "@parent" {
					r.add(path, "", "duplicate_identity", fmt.Sprintf("%s identity %q is already defined in %s", collection.Name, id, strings.Join(prior, ", ")))
				} else {
					indices[collection.Name][id] = append(indices[collection.Name][id], path)
				}
			}
		}
		var walk func(any, string)
		walk = func(value any, pointer string) {
			switch value := value.(type) {
			case map[string]any:
				kind := ""
				if rawType, exists := value["$type"]; exists {
					typeString, ok := rawType.(string)
					if !ok || typeString == "" {
						r.add(path, pointer+"/$type", "schema", "$type must be a nonempty string")
					} else {
						kind = typeName(typeString)
					}
				}
				if schema := p.ModelSchemas[kind]; schema != "" && (pointer != "" || !checked[schema]) {
					if err := schemas[schema].Validate(value); err != nil {
						r.add(path, pointer, "schema", err.Error())
					}
				}
				for _, rule := range rulesByModel[kind] {
					reference := value[rule.Field]
					if reference == nil {
						continue
					}
					var collect func(any, string)
					collect = func(value any, pointer string) {
						switch value := value.(type) {
						case string:
							if value != "" {
								pending = append(pending, pendingReference{path, pointer, value, rule})
							}
						case []any:
							for i, item := range value {
								itemPointer := pointer + "/" + strconv.Itoa(i)
								if _, ok := item.(string); !ok {
									r.add(path, itemPointer, "reference_type", "reference array items must be strings")
								} else {
									collect(item, itemPointer)
								}
							}
						default:
							r.add(path, pointer, "reference_type", "reference must be a string or an array of strings")
						}
					}
					collect(reference, pointer+"/"+pointerToken(rule.Field))
				}
				keys := make([]string, 0, len(value))
				for key := range value {
					keys = append(keys, key)
				}
				sort.Strings(keys)
				for _, key := range keys {
					if key != "$type" {
						walk(value[key], pointer+"/"+pointerToken(key))
					}
				}
			case []any:
				for i, item := range value {
					walk(item, pointer+"/"+strconv.Itoa(i))
				}
			}
		}
		walk(object, "")
	}
	if includeRelations {
		r.Backlinks = map[string][]location{}
	}
	for _, reference := range pending {
		r.ReferencesChecked++
		value := reference.Value
		if alias, exists := reference.Rule.Aliases[value]; exists {
			value = alias
		}
		targets := indices[reference.Rule.Target][value]
		external := false
		if len(targets) == 0 {
			_, external = reference.Rule.ExternalSymbols[reference.Value]
		}
		if external {
			r.ExternalReferences++
		}
		if len(targets) == 0 && !external {
			r.add(reference.File, reference.Pointer, "missing_reference", fmt.Sprintf("%s record %q does not exist", reference.Rule.Target, reference.Value))
			continue
		}
		if includeRelations {
			if targets == nil {
				targets = []string{}
			}
			r.Relations = append(r.Relations, relation{reference.File, reference.Pointer, reference.Value, reference.Rule.Target, value, targets, external})
			for _, target := range targets {
				r.Backlinks[target] = append(r.Backlinks[target], location{reference.File, reference.Pointer})
			}
		}
	}
	// Capture metadata is informational and does not restrict which data versions are valid.
	manifestPath := filepath.Join(filepath.Dir(filepath.Clean(dataDirectory)), "manifest.json")
	if _, err := os.Stat(manifestPath); err == nil {
		value, err := readJSON(manifestPath)
		if err != nil {
			r.add("../manifest.json", "", "json", err.Error())
		} else if manifest, ok := value.(map[string]any); ok {
			r.GameVersion, _ = manifest["gameVersion"].(string)
		} else {
			r.add("../manifest.json", "", "schema", "manifest must be a JSON object")
		}
	} else if !os.IsNotExist(err) {
		r.add("../manifest.json", "", "read", err.Error())
	}
	sort.Slice(r.Errors, func(i, j int) bool {
		a, b := r.Errors[i], r.Errors[j]
		return a.File+"\x00"+a.Pointer+"\x00"+a.Code+"\x00"+a.Message < b.File+"\x00"+b.Pointer+"\x00"+b.Code+"\x00"+b.Message
	})
	r.Valid = len(r.Errors) == 0
	if !r.Valid {
		return r, 1
	}
	return r, 0
}

func run(args []string, stdout, stderr io.Writer) int {
	flags := flag.NewFlagSet("atlas-validate", flag.ContinueOnError)
	flags.SetOutput(stderr)
	data := flags.String("data", "", "raw game-data directory")
	profile := flags.String("profile", "", "directory containing game-profile.json")
	format := flags.String("format", "json", "output format: json or text")
	relations := flags.Bool("relations", false, "include resolved references and file backlinks in JSON output")
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if *data == "" || *profile == "" || flags.NArg() != 0 || (*format != "json" && *format != "text") || (*relations && *format != "json") {
		fmt.Fprintln(stderr, "Usage: atlas-validate --data <game-data> --profile <profile> [--format json|text] [--relations]")
		return 2
	}
	result, status := validate(*data, *profile, *relations)
	if *format == "text" {
		for _, error := range result.Errors {
			fmt.Fprintf(stdout, "%s#%s: %s: %s\n", error.File, error.Pointer, error.Code, error.Message)
		}
		fmt.Fprintf(stdout, "valid=%t; files=%d; references=%d; external=%d; errors=%d\n", result.Valid, result.FilesChecked, result.ReferencesChecked, result.ExternalReferences, len(result.Errors))
	} else {
		encoder := json.NewEncoder(stdout)
		encoder.SetIndent("", "  ")
		if err := encoder.Encode(result); err != nil {
			fmt.Fprintln(stderr, err)
			return 2
		}
	}
	return status
}

func main() { os.Exit(run(os.Args[1:], os.Stdout, os.Stderr)) }
