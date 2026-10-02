The CranioZ Tools system must adhere to the following principles:

#### 1. A Tool is an interaction interface

It is not part of the domain and must not contain complex clinical or geometric logic.

#### 2. A Tool is not a Command

A Tool may create or execute a Command, but the Command must remain independent of the UI.

#### 3. A Tool does not structurally belong to an Area

A Tool may be presented in any compatible Area or Editor.

#### 4. A Tool must be contextual

Its availability may depend on the current state of the project, selection, Editor, or module.

#### 5. A Tool must have a stable identity

The identifier must be independent of the text and position within the interface.

#### 6. A Tool must be discoverable

Tools must be registrable and queryable by the framework.

#### 7. A Tool must be reusable

The same operation must be triggerable via different mechanisms.

#### 8. An interactive Tool must have its own lifecycle

The temporary state of the interaction must be separate from the Tool's permanent definition.

#### 9. Validation must not depend on the UI

Critical operations must be validated at the application and domain layers.

#### 10. Plugins may provide Tools

The mechanism must work for both internal modules and external extensions.

#### 11. Tools must not be aware of the Workspace organization

The Tool defines the interaction; the Workspace determines where it is presented.

#### 12. Commands must remain independent of Tools

The same operation must be usable by the UI, workflows, scripts, and automation.

#### 13. Tools must be compatible with automation

The architecture must allow the same operations to be used in the future by workflows, scripts, and MCP.