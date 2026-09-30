package atlasvalidate

import "github.com/google/jsonschema-go/jsonschema"

const profileFormatVersion = 3
const validatorFormatVersion = 3
const Version = "3.0.0"

type documentRef struct {
	File, Schema string
}

type manifest struct {
	FormatVersion, ValidatorFormatVersion int
	ID, Revision, Game, ProposalSchema    string
	Documents                             map[string]documentRef
	CaptureMetadata                       *metadataBinding
}

type collection struct {
	Name, Path, IDField, Schema string
	Layout                      *recordLayout
	Enabled                     *bool
	RequireWhen                 []requirement
}

type requirement struct {
	Collection, SelectorSchema, Field string
	Models                            []string
}
type metadataBinding struct {
	Base, Path string
	Fields     map[string]string
}
type typeIdentity struct{ Field, Encoding string }
type scoringDocument struct {
	Collection, FamilyField string
	Weights                 map[string]float64
}

type recordLayout struct {
	Depth                  int
	ParentField, StemField string
}

type scope struct {
	Name, Collection, RootSchema, MemberSchema, EdgesField, TargetField string
}

type collectionsDocument struct {
	Collections    []collection
	Scopes         []scope
	UnmatchedFiles string
}

type referenceRule struct {
	Models          []string
	Field, Target   string
	ExternalSymbols map[string]string
	Aliases         map[string]string
}

type referencesDocument struct {
	References []referenceRule
}

type mechanic struct {
	ID, Schema, Role string
	Models           []string
}

type mechanicsDocument struct {
	UnknownModels string
	TypeIdentity  typeIdentity
	Mechanics     []mechanic
}

type progressionLimits struct {
	PathCount, MaxTier, MaxPurchasedPaths, SecondaryTierLimit, MaxPathsAboveSecondaryTier int
}

type rule struct {
	ID, Operation, Scope, TiersField, FamilyField string
	Limits                                        progressionLimits
	RequireCompleteStates                         bool
}

type rulesDocument struct {
	Rules []rule
}

type unitDefinition struct {
	ID, Dimension, Description string
}

type unitBinding struct {
	Models               []string
	Field, Unit, Meaning string
}

type unitsDocument struct {
	Units    []unitDefinition
	Bindings []unitBinding
}

type profile struct {
	Manifest       manifest
	TypeIdentity   typeIdentity
	Scoring        scoringDocument
	Collections    []collection
	Scopes         []scope
	UnmatchedFiles string
	References     []referenceRule
	Mechanics      []mechanic
	ModelSchemas   map[string]string
	UnknownModels  string
	Rules          []rule
	Units          unitsDocument
	Identity       ProfileIdentity
}

type record struct {
	File  string
	Value map[string]any
}

type recordIndex map[string]map[string][]record

type schemaIndex map[string]*jsonschema.Resolved
