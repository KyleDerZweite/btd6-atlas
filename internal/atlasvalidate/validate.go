// Package atlasvalidate checks records against a self-contained data Profile.
package atlasvalidate

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type pendingReference struct {
	File, Pointer, Value string
	Rule                 referenceRule
}

func matches(path, collectionPath string) bool {
	return collectionPath == "." || path == collectionPath || strings.HasPrefix(path, collectionPath+"/")
}

// Validate reads game-data and its Profile without modifying either directory.
// Status is 0 for valid data, 1 for invalid data, and 2 for invocation/Profile errors.
func Validate(dataDirectory, profileDirectory string, includeRelations bool) (Report, int) {
	r := Report{Errors: []Diagnostic{}, Checker: checker(), Rules: []RuleResult{}, Coverage: Coverage{UnboundModelTypes: []ModelCount{}}}
	p, schemas, err := loadProfile(profileDirectory)
	if err != nil {
		file := "manifest.json"
		var docErr *profileDocumentError
		if errors.As(err, &docErr) {
			file = docErr.File
		}
		r.add(file, "", "profile", err.Error())
		return r, 2
	}
	r.Game = p.Manifest.Game
	r.Profile = &p.Identity
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
	records := recordIndex{}
	for _, s := range p.Scopes {
		records[s.Collection] = map[string][]record{}
	}
	unknownModels := map[string]int{}
	unitsByModel := map[string][]unitBinding{}
	for _, binding := range p.Units.Bindings {
		for _, model := range binding.Models {
			unitsByModel[model] = append(unitsByModel[model], binding)
		}
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
				if scoped := records[collection.Name]; scoped != nil {
					scoped[id] = append(scoped[id], record{File: path, Value: object})
				}
				if prior, exists := indices[collection.Name][id]; exists && collection.IDField != "@parent" {
					r.add(path, "", "duplicate_identity", fmt.Sprintf("%s identity %q is already defined in %s", collection.Name, id, strings.Join(prior, ", ")))
				} else {
					indices[collection.Name][id] = append(indices[collection.Name][id], path)
				}
			}
		}
		if len(checked) > 0 {
			r.Coverage.FilesWithSchema++
		} else {
			r.Coverage.FilesWithoutSchema++
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
				if kind != "" {
					if p.ModelSchemas[kind] != "" {
						r.Coverage.BoundModelInstances++
					} else {
						r.Coverage.UnboundModelInstances++
						unknownModels[kind]++
						if p.UnknownModels == "error" {
							r.add(path, pointer+"/$type", "unknown_model", fmt.Sprintf("model %q has no mechanic schema binding", kind))
						}
					}
					for _, binding := range unitsByModel[kind] {
						if number, exists := value[binding.Field]; exists {
							r.Coverage.UnitBindingsChecked++
							if _, ok := number.(float64); !ok {
								r.add(path, pointer+"/"+pointerToken(binding.Field), "unit_type", fmt.Sprintf("field bound to unit %q must be numeric", binding.Unit))
							}
						}
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
		r.Backlinks = map[string][]Location{}
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
			r.Relations = append(r.Relations, Relation{reference.File, reference.Pointer, reference.Value, reference.Rule.Target, value, targets, external})
			for _, target := range targets {
				r.Backlinks[target] = append(r.Backlinks[target], Location{reference.File, reference.Pointer})
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
			capture := &CaptureIdentity{GameVersion: r.GameVersion}
			capture.SteamBuildID, _ = manifest["steamBuildId"].(string)
			capture.ModHelperVersion, _ = manifest["modHelperVersion"].(string)
			capture.AtlasExporterVersion, _ = manifest["atlasExporterVersion"].(string)
			if raw, err := os.ReadFile(manifestPath); err == nil {
				capture.ManifestSHA256 = digest(raw)
			}
			r.Capture = capture
		} else {
			r.add("../manifest.json", "", "schema", "manifest must be a JSON object")
		}
	} else if !os.IsNotExist(err) {
		r.add("../manifest.json", "", "read", err.Error())
	}
	for kind, count := range unknownModels {
		r.Coverage.UnboundModelTypes = append(r.Coverage.UnboundModelTypes, ModelCount{Type: kind, Instances: count})
	}
	sort.Slice(r.Coverage.UnboundModelTypes, func(i, j int) bool {
		return r.Coverage.UnboundModelTypes[i].Type < r.Coverage.UnboundModelTypes[j].Type
	})
	r.IntegrityValid = len(r.Errors) == 0
	checkRules(p, schemas, records, &r)
	r.RulesValid = true
	for _, result := range r.Rules {
		if result.Errors > 0 {
			r.RulesValid = false
		}
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
