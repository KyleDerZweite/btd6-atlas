# Atlas domain terms

A Profile is the reusable set of schemas, mechanic bindings, reference declarations and rules applied to game-data. It contains requirements rather than captured Tower instances.

A capture is recorded game-data with its source versions, exporter identity and hashes. A compatible Profile can validate multiple captures.

A collection layout is a Profile requirement for the depth of record files and their folder or filename bindings. Tower family folders and state filenames can therefore be checked against recorded identities.

A Tower family groups records for one base Tower identity. It can contain ordinary builds, a paragon and temporary forms.

A permanent build is a Tower state reachable through ordinary purchase links from a selected base Tower. Its tier tuple identifies the build within that progression family.

A purchase transition is a link from one permanent build to its target build and upgrade record. The upgrade record supplies the purchase identity and price.

A temporary form is behavior active under temporary conditions, represented by mutations, replacement attacks or separate Tower records. It is not an ordinary purchase and may reuse a permanent build's tier tuple.

A mechanic binding associates raw model classes with a schema. It declares structural coverage without claiming a runtime implementation.

Validation coverage describes which schemas, references and rules checked which records. A passing result applies to those declared requirements.
