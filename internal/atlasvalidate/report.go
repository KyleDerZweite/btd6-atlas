package atlasvalidate

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"runtime/debug"
	"sync"
)

type Diagnostic struct {
	File    string `json:"file"`
	Pointer string `json:"pointer"`
	Code    string `json:"code"`
	Message string `json:"message"`
	RuleID  string `json:"rule,omitempty"`
}

type ProfileIdentity struct {
	ID            string `json:"id"`
	Revision      string `json:"revision"`
	FormatVersion int    `json:"formatVersion"`
	SHA256        string `json:"sha256"`
	Files         int    `json:"files"`
}

type CheckerIdentity struct {
	Name             string `json:"name"`
	Version          string `json:"version"`
	GoVersion        string `json:"goVersion,omitempty"`
	Revision         string `json:"revision,omitempty"`
	Modified         bool   `json:"modified"`
	ExecutableSHA256 string `json:"executableSha256,omitempty"`
}

type CaptureIdentity struct {
	GameVersion          string `json:"gameVersion,omitempty"`
	SteamBuildID         string `json:"steamBuildId,omitempty"`
	ModHelperVersion     string `json:"modHelperVersion,omitempty"`
	AtlasExporterVersion string `json:"atlasExporterVersion,omitempty"`
	ManifestSHA256       string `json:"manifestSha256,omitempty"`
}

type ModelCount struct {
	Type      string `json:"type"`
	Instances int    `json:"instances"`
}

type Coverage struct {
	FilesWithSchema       int          `json:"filesWithSchema"`
	FilesWithoutSchema    int          `json:"filesWithoutSchema"`
	BoundModelInstances   int          `json:"boundModelInstances"`
	UnboundModelInstances int          `json:"unboundModelInstances"`
	UnboundModelTypes     []ModelCount `json:"unboundModelTypes"`
	UnitBindingsChecked   int          `json:"unitBindingsChecked"`
}

type RuleResult struct {
	ID                 string `json:"id"`
	Operation          string `json:"operation"`
	Scope              string `json:"scope"`
	Roots              int    `json:"roots"`
	RecordsChecked     int    `json:"recordsChecked"`
	TransitionsChecked int    `json:"transitionsChecked"`
	ExpectedStates     int    `json:"expectedStates"`
	Errors             int    `json:"errors"`
	OutOfScopeRecords  int    `json:"outOfScopeRecords"`
}

type Report struct {
	Valid              bool                  `json:"valid"`
	IntegrityValid     bool                  `json:"integrityValid"`
	RulesValid         bool                  `json:"rulesValid"`
	Game               string                `json:"game,omitempty"`
	GameVersion        string                `json:"gameVersion,omitempty"`
	Profile            *ProfileIdentity      `json:"profile,omitempty"`
	Checker            CheckerIdentity       `json:"checker"`
	Capture            *CaptureIdentity      `json:"capture,omitempty"`
	FilesChecked       int                   `json:"filesChecked"`
	ReferencesChecked  int                   `json:"referencesChecked"`
	ExternalReferences int                   `json:"externalReferences"`
	Coverage           Coverage              `json:"coverage"`
	Rules              []RuleResult          `json:"rules"`
	Errors             []Diagnostic          `json:"errors"`
	Relations          []Relation            `json:"relations,omitempty"`
	Backlinks          map[string][]Location `json:"backlinks,omitempty"`
}

type Location struct {
	File    string `json:"file"`
	Pointer string `json:"pointer"`
}

type Relation struct {
	File             string   `json:"file"`
	Pointer          string   `json:"pointer"`
	Value            string   `json:"value"`
	TargetCollection string   `json:"targetCollection"`
	TargetID         string   `json:"targetId"`
	TargetFiles      []string `json:"targetFiles"`
	External         bool     `json:"external,omitempty"`
}

func (r *Report) add(file, pointer, code, message string) {
	r.Errors = append(r.Errors, Diagnostic{File: file, Pointer: pointer, Code: code, Message: message})
}

func (r *Report) addRule(id, file, pointer, code, message string) {
	r.Errors = append(r.Errors, Diagnostic{File: file, Pointer: pointer, Code: code, Message: message, RuleID: id})
}

func digest(raw []byte) string {
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

var checkerOnce sync.Once
var checkerIdentity CheckerIdentity

func checker() CheckerIdentity {
	checkerOnce.Do(func() {
		checkerIdentity = CheckerIdentity{Name: "atlas-validate", Version: Version}
		if info, ok := debug.ReadBuildInfo(); ok {
			checkerIdentity.GoVersion = info.GoVersion
			for _, setting := range info.Settings {
				switch setting.Key {
				case "vcs.revision":
					checkerIdentity.Revision = setting.Value
				case "vcs.modified":
					checkerIdentity.Modified = setting.Value == "true"
				}
			}
		}
		if path, err := os.Executable(); err == nil {
			if raw, err := os.ReadFile(path); err == nil {
				checkerIdentity.ExecutableSHA256 = digest(raw)
			}
		}
	})
	return checkerIdentity
}
