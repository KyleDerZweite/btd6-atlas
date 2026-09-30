package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/KyleDerZweite/btd6-atlas/internal/atlasvalidate"
)

func TestCLI(t *testing.T) {
	data := t.TempDir()
	if err := os.WriteFile(filepath.Join(data, "textTable.json"), []byte(`{"hello":"Hello"}`), 0644); err != nil {
		t.Fatal(err)
	}
	profile := t.TempDir()
	source := filepath.Join("..", "..", "profile")
	entries, err := os.ReadDir(source)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(source, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(profile, entry.Name()), raw, 0644); err != nil {
			t.Fatal(err)
		}
	}
	// This CLI fixture checks only collection integrity, without a Tower corpus.
	if err := os.WriteFile(filepath.Join(profile, "rules.json"), []byte(`{"rules":[]}`), 0644); err != nil {
		t.Fatal(err)
	}
	base := []string{"--data", data, "--profile", profile}
	var stdout, stderr bytes.Buffer
	if status := run(base, &stdout, &stderr); status != 0 {
		t.Fatalf("CLI exit=%d, output=%s, stderr=%s", status, stdout.String(), stderr.String())
	}
	var report atlasvalidate.Report
	if err := json.Unmarshal(stdout.Bytes(), &report); err != nil || !report.Valid || report.Profile == nil || report.Checker.Version == "" {
		t.Fatalf("invalid report: %s", stdout.String())
	}
	stdout.Reset()
	if status := run(append(base, "--format", "text"), &stdout, &stderr); status != 0 || !strings.Contains(stdout.String(), "valid=true; integrity=true; rules=true") {
		t.Fatalf("invalid text output: %s", stdout.String())
	}
	stdout.Reset()
	if status := run(append(base, "--relations"), &stdout, &stderr); status != 0 || json.Unmarshal(stdout.Bytes(), &report) != nil {
		t.Fatalf("relations output failed: %s", stdout.String())
	}
	if err := os.Remove(filepath.Join(data, "textTable.json")); err != nil {
		t.Fatal(err)
	}
	stdout.Reset()
	if status := run(base, &stdout, &stderr); status != 1 || json.Unmarshal(stdout.Bytes(), &report) != nil || report.Valid {
		t.Fatalf("invalid data did not exit 1: %s", stdout.String())
	}
}

func TestCLIArguments(t *testing.T) {
	cases := [][]string{
		nil,
		{"--data", "data"},
		{"--data", "data", "--profile", "profile", "--format", "xml"},
		{"--data", "data", "--profile", "profile", "--format", "text", "--relations"},
		{"--data", "data", "--profile", "profile", "extra"},
		{"--unknown"},
	}
	for _, args := range cases {
		var stdout, stderr bytes.Buffer
		if status := run(args, &stdout, &stderr); status != 2 {
			t.Errorf("args=%v exit=%d", args, status)
		}
	}
	var stdout, stderr bytes.Buffer
	if status := run([]string{"--help"}, &stdout, &stderr); status != 0 {
		t.Errorf("help exit=%d", status)
	}
}
