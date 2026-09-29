package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func writeFixture(t *testing.T, root, name string, value any) {
	t.Helper()
	path := filepath.Join(root, filepath.FromSlash(name))
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, raw, 0644); err != nil {
		t.Fatal(err)
	}
}

func fixture(t *testing.T) (string, string) {
	t.Helper()
	root := t.TempDir()
	data := filepath.Join(root, "game-data")
	profileDir := filepath.Join(root, "profile")
	if err := os.MkdirAll(profileDir, 0755); err != nil {
		t.Fatal(err)
	}
	schema, err := os.ReadFile(filepath.Join("..", "..", "profile", "schema.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(profileDir, "schema.json"), schema, 0644); err != nil {
		t.Fatal(err)
	}
	writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel, Assembly-CSharp", "name": "a", "target": "b"})
	writeFixture(t, data, "Things/b.json", map[string]any{"$type": "Example.ThingModel, Assembly-CSharp", "name": "b"})
	writeFixture(t, data, "text.json", map[string]any{"hello": "Hello"})
	writeFixture(t, profileDir, "game-profile.json", map[string]any{
		"formatVersion": 1, "game": "fixture", "schemaFile": "schema.json", "requiredFiles": []string{"text.json"},
		"collections":  []any{map[string]any{"name": "things", "path": "Things", "idField": "name", "schema": "namedModel"}, map[string]any{"name": "text", "path": "text.json", "idField": "@keys", "schema": "stringTable"}},
		"modelSchemas": map[string]string{"WeaponModel": "weapon", "AttackModel": "attack"}, "reading": map[string]any{},
		"references": []any{map[string]any{"models": []string{"ThingModel"}, "field": "target", "target": "things", "aliases": map[string]string{"legacy-b": "b"}, "externalSymbols": map[string]string{"runtime-only": "This test symbol has no file definition."}}},
	})
	return data, profileDir
}

func hasError(r report, code, file, pointer string) bool {
	for _, error := range r.Errors {
		if error.Code == code && (file == "" || error.File == file) && (pointer == "" || error.Pointer == pointer) {
			return true
		}
	}
	return false
}

func TestValidDataAndReferenceConventions(t *testing.T) {
	for _, target := range []string{"b", "legacy-b", "runtime-only"} {
		t.Run(target, func(t *testing.T) {
			data, profileDir := fixture(t)
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel, Assembly-CSharp", "name": "a", "target": target})
			r, status := validate(data, profileDir, false)
			if status != 0 || !r.Valid || r.FilesChecked != 3 || r.ReferencesChecked != 1 {
				t.Fatalf("unexpected result: %+v, status=%d", r, status)
			}
		})
	}
}

func TestBrokenData(t *testing.T) {
	cases := []struct {
		name, code, file, pointer string
		change                    func(*testing.T, string)
	}{
		{"missing target", "missing_reference", "Things/a.json", "/target", func(t *testing.T, data string) {
			if err := os.Remove(filepath.Join(data, "Things/b.json")); err != nil {
				t.Fatal(err)
			}
		}},
		{"dangling name without file deletion", "missing_reference", "Things/a.json", "/target", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel", "name": "a", "target": "missing"})
		}},
		{"nested missing target", "missing_reference", "Things/a.json", "/child/target", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel", "name": "a", "child": map[string]any{"$type": "Example.ThingModel", "name": "local", "target": "missing"}})
		}},
		{"alias target removed", "missing_reference", "Things/a.json", "/target", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel", "name": "a", "target": "legacy-b"})
			if err := os.Remove(filepath.Join(data, "Things/b.json")); err != nil {
				t.Fatal(err)
			}
		}},
		{"required top-level file", "missing_file", "text.json", "", func(t *testing.T, data string) {
			if err := os.Remove(filepath.Join(data, "text.json")); err != nil {
				t.Fatal(err)
			}
		}},
		{"duplicate identity", "duplicate_identity", "Things/b.json", "", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/b.json", map[string]any{"$type": "Example.ThingModel", "name": "a"})
		}},
		{"invalid nested weapon interval", "schema", "Things/a.json", "/weapon", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel", "name": "a", "weapon": map[string]any{"$type": "Example.WeaponModel", "rate": "fast", "projectile": nil, "emission": nil}})
		}},
		{"wrong model type in weapon slot", "schema", "Things/a.json", "/attack", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel", "name": "a", "attack": map[string]any{
				"$type": "Example.AttackModel", "range": 40,
				"weapons": []any{map[string]any{"$type": "Example.WrongModel", "rate": 1, "projectile": nil, "emission": nil}},
			}})
		}},
		{"invalid type discriminator", "schema", "Things/a.json", "/$type", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": 3, "name": "a"})
		}},
		{"invalid reference type", "reference_type", "Things/a.json", "/target", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel", "name": "a", "target": 3})
		}},
		{"invalid reference array", "reference_type", "Things/a.json", "/target/0", func(t *testing.T, data string) {
			writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel", "name": "a", "target": []any{[]string{"b"}}})
		}},
		{"duplicate JSON key", "json", "Things/a.json", "", func(t *testing.T, data string) {
			if err := os.WriteFile(filepath.Join(data, "Things/a.json"), []byte(`{"$type":"Example.ThingModel","name":"a","name":"b"}`), 0644); err != nil {
				t.Fatal(err)
			}
		}},
		{"trailing JSON value", "json", "Things/a.json", "", func(t *testing.T, data string) {
			if err := os.WriteFile(filepath.Join(data, "Things/a.json"), []byte(`{"$type":"Example.ThingModel","name":"a"} {}`), 0644); err != nil {
				t.Fatal(err)
			}
		}},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			data, profileDir := fixture(t)
			test.change(t, data)
			r, status := validate(data, profileDir, false)
			if status != 1 || r.Valid || !hasError(r, test.code, test.file, test.pointer) {
				t.Fatalf("expected %s at %s#%s, got %+v, status=%d", test.code, test.file, test.pointer, r, status)
			}
		})
	}
}

func TestDynamicDataAndRelations(t *testing.T) {
	data, profileDir := fixture(t)
	// Names come from records, so moving a file does not invalidate references.
	if err := os.Rename(filepath.Join(data, "Things/b.json"), filepath.Join(data, "Things/renamed.json")); err != nil {
		t.Fatal(err)
	}
	writeFixture(t, data, "Things/c.json", map[string]any{"$type": "Example.ThingModel", "name": "c", "target": "legacy-b"})
	writeFixture(t, data, "extra.json", map[string]any{"customField": true})
	writeFixture(t, filepath.Dir(data), "manifest.json", map[string]any{"gameVersion": "another-version", "totalFiles": 999})
	r, status := validate(data, profileDir, true)
	if status != 0 || !r.Valid || r.FilesChecked != 5 || r.GameVersion != "another-version" || len(r.Relations) != 2 {
		t.Fatalf("dynamic data rejected: %+v, status=%d", r, status)
	}
	if len(r.Backlinks["Things/renamed.json"]) != 2 || r.Relations[1].TargetID != "b" || r.Relations[1].Value != "legacy-b" {
		t.Fatalf("incorrect graph: %+v", r)
	}
	// Removing an unreferenced record is allowed; no baseline inventory is needed.
	if err := os.Remove(filepath.Join(data, "Things/c.json")); err != nil {
		t.Fatal(err)
	}
	r, status = validate(data, profileDir, false)
	if status != 0 || !r.Valid || r.FilesChecked != 4 || len(r.Relations) != 0 || len(r.Backlinks) != 0 {
		t.Fatalf("different collection size rejected: %+v, status=%d", r, status)
	}
}

func TestFamilyRelations(t *testing.T) {
	data, profileDir := fixture(t)
	value, err := readJSON(filepath.Join(profileDir, "game-profile.json"))
	if err != nil {
		t.Fatal(err)
	}
	p := value.(map[string]any)
	p["collections"] = append(p["collections"].([]any), map[string]any{"name": "families", "path": "Things", "idField": "@parent", "schema": "namedModel"})
	p["references"] = append(p["references"].([]any), map[string]any{"models": []string{"ThingModel"}, "field": "family", "target": "families"})
	writeFixture(t, profileDir, "game-profile.json", p)
	writeFixture(t, data, "Things/a.json", map[string]any{"$type": "Example.ThingModel", "name": "a", "family": "Things"})
	r, status := validate(data, profileDir, true)
	if status != 0 || len(r.Relations) != 1 || len(r.Relations[0].TargetFiles) != 2 || len(r.Backlinks["Things/b.json"]) != 1 {
		t.Fatalf("incorrect family graph: %+v, status=%d", r, status)
	}
}

func TestInvalidProfileAndCLI(t *testing.T) {
	data, profileDir := fixture(t)
	profilePath := filepath.Join(profileDir, "game-profile.json")
	raw, err := os.ReadFile(profilePath)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(profilePath, bytes.Replace(raw, []byte(`"target":"things"`), []byte(`"target":"unknown"`), 1), 0644); err != nil {
		t.Fatal(err)
	}
	r, status := validate(data, profileDir, false)
	if status != 2 || !hasError(r, "profile", "", "") {
		t.Fatalf("invalid profile accepted: %+v, status=%d", r, status)
	}
	data, profileDir = fixture(t)
	var stdout, stderr bytes.Buffer
	if status := run([]string{"--data", data, "--profile", profileDir}, &stdout, &stderr); status != 0 {
		t.Fatalf("CLI failed: %s", stderr.String())
	}
	var output report
	if err := json.Unmarshal(stdout.Bytes(), &output); err != nil || !output.Valid {
		t.Fatalf("invalid JSON output: %s", stdout.String())
	}
	stdout.Reset()
	if status := run([]string{"--data", data, "--profile", profileDir, "--format", "text"}, &stdout, &stderr); status != 0 || !strings.Contains(stdout.String(), "valid=true") {
		t.Fatalf("invalid text output: %s", stdout.String())
	}
	if status := run(nil, &stdout, &stderr); status != 2 {
		t.Fatalf("missing arguments exit=%d", status)
	}
	stdout.Reset()
	if status := run([]string{"--data", data, "--profile", profileDir, "--relations"}, &stdout, &stderr); status != 0 {
		t.Fatalf("relations CLI failed: %s", stderr.String())
	}
	if err := json.Unmarshal(stdout.Bytes(), &output); err != nil || len(output.Relations) != 1 || len(output.Backlinks["Things/b.json"]) != 1 {
		t.Fatalf("invalid graph output: %s", stdout.String())
	}
}
