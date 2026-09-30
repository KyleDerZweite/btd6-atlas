# Atlas domain terms

A Profile combines reusable schemas with game-specific mechanic bindings, reference declarations and rules applied to game-data. It contains requirements rather than captured Tower instances.

A capture is recorded game-data with its source versions, exporter identity and hashes. A compatible Profile can validate multiple captures.

A Profile collection is a logical group of records with an identity and schema. Its logical name is independent of its source path and raw model names.

A collection layout is a Profile requirement for the depth of record files and their folder or filename bindings. Tower family folders and state filenames can therefore be checked against recorded identities.

A Tower family groups records for one base Tower identity. It can contain ordinary builds, a paragon and temporary forms.

A permanent state belongs to a Tower family's declared progression. A purchase build uses a tier tuple; a levelled state uses its level.

A purchase transition is a link from one permanent build to its target build and upgrade record. The upgrade record supplies the purchase identity and price.

A temporary form is behavior active under temporary conditions, represented by mutations, replacement attacks or separate Tower records. It is not an ordinary purchase and may reuse a permanent build's tier tuple.

A mechanic binding associates source model classes and field names with a shared schema. It declares structural coverage without claiming a runtime implementation.

Validation coverage describes which schemas, references and rules checked which records. A passing result applies to those declared requirements.

A record type is a logical category selected by Profile rules, such as a levelled Tower, subordinate Tower or alternate form. It is distinct from the source model class.

A model class is the source type of a serialized object, identified through a configured field and encoding. It can describe gameplay behavior, presentation or a supporting value.

A progression policy defines the permanent states and transitions allowed for a record type. Experience levels and purchase paths can use different policies while sharing a Tower shape.

A schema view is the temporary generic representation built from Profile field bindings for validation. It does not replace or rewrite raw game-data.

Model-schema coverage is the proportion of detected model instances with declared schema bindings. It does not establish simulation fidelity or gameplay balance.
