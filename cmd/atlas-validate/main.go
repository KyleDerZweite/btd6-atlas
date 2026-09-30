// atlas-validate checks game-data against a local Profile.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"

	"github.com/KyleDerZweite/btd6-atlas/internal/atlasvalidate"
)

func run(args []string, stdout, stderr io.Writer) int {
	flags := flag.NewFlagSet("atlas-validate", flag.ContinueOnError)
	flags.SetOutput(stderr)
	data := flags.String("data", "", "raw game-data directory")
	profile := flags.String("profile", "", "self-contained Profile directory")
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
	result, status := atlasvalidate.Validate(*data, *profile, *relations)
	if *format == "text" {
		for _, error := range result.Errors {
			fmt.Fprintf(stdout, "%s#%s: %s: %s\n", error.File, error.Pointer, error.Code, error.Message)
		}
		fmt.Fprintf(stdout, "valid=%t; integrity=%t; rules=%t; files=%d; references=%d; external=%d; errors=%d\n", result.Valid, result.IntegrityValid, result.RulesValid, result.FilesChecked, result.ReferencesChecked, result.ExternalReferences, len(result.Errors))
		for _, rule := range result.Rules {
			fmt.Fprintf(stdout, "rule=%s; roots=%d; records=%d; transitions=%d; expectedStates=%d; excluded=%d; errors=%d\n", rule.ID, rule.Roots, rule.RecordsChecked, rule.TransitionsChecked, rule.ExpectedStates, rule.OutOfScopeRecords, rule.Errors)
		}
		fmt.Fprintf(stdout, "coverage: schemaFiles=%d; layoutFiles=%d; unboundModelTypes=%d; unitBindings=%d\n", result.Coverage.FilesWithSchema, result.Coverage.LayoutFilesChecked, len(result.Coverage.UnboundModelTypes), result.Coverage.UnitBindingsChecked)
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
