# Just-in-Time Testing Implementation Plan

## Purpose
This document defines a practical implementation plan for a Just-in-Time testing system aimed at C# and Visual Studio workflows.

The goal is to add fast, change-aware, disposable test generation to AI-assisted development without turning every temporary check into a permanent maintenance burden.

## Scope
This plan covers:
- A shared core engine for diff analysis, risk classification, test generation, and execution.
- A local companion CLI used by the extension for analysis and test execution.
- A Visual Studio extension that provides the primary developer experience.
- A pre-commit entry point for local enforcement when enabled from the extension.

This plan does not cover:
- Full IDE integration for editors other than Visual Studio.
- CI or pull request pipeline integration.
- Automatic promotion of all generated tests into the permanent suite.
- Replacing the existing permanent unit and integration test strategy.

## Design Principles
- Keep the execution logic outside the extension.
- Use the same engine in local extension actions and optional pre-commit workflows.
- Prefer deterministic templates before LLM-generated freeform tests.
- Treat AI-assisted generation as an optional provider-backed feature, not a required dependency.
- Generate disposable tests into a scratch location, not into committed test projects by default.
- Promote a generated test to the permanent suite only when it proves a durable business rule or exposes a stable regression.
- Keep all local workflows fast enough for day-to-day development.

## Target Architecture
The system is split into three layers.

### 1. Core Engine
The core engine is a .NET library responsible for:
- Reading git diffs.
- Mapping changed lines to C# symbols via Roslyn.
- Classifying risk based on the type of change.
- Generating temporary tests from templates.
- Running generated tests and selected impacted permanent tests.
- Producing machine-readable and human-readable results.

### 2. CLI
The CLI is a thin wrapper over the core engine.

The CLI will support commands such as:
- `jit-test analyze`
- `jit-test generate`
- `jit-test run`
- `jit-test pre-commit`

### 3. Visual Studio Extension
The Visual Studio extension is the local UX layer.

The extension will:
- Detect the current solution and active document.
- Trigger JiT analysis for the current file or current change.
- Display generated test summaries and failures.
- Offer one-click rerun and optional promotion to a permanent test.
- Install or configure the repo-local pre-commit hook when requested.

## Core Engine Components

### Diff Analyzer
Responsibilities:
- Read staged changes for pre-commit.
- Filter to relevant files such as `.cs`, `.csproj`, `.props`, `.targets`, and selected config files.

Outputs:
- Changed files.
- Changed hunks.
- Changed line ranges.

### Roslyn Impact Analyzer
Responsibilities:
- Map changed lines to methods, constructors, properties, classes, and public APIs.
- Detect when a change affects signatures, nullability, attributes, async flow, control flow, serialization contracts, or dependency boundaries.

Outputs:
- Impacted symbols.
- Change classifications.
- Risk signals.

### Risk Engine
Responsibilities:
- Convert symbol and change data into concrete test intents.
- Decide whether a symbol should get boundary tests, branch probes, async behavior tests, exception checks, or contract tests.

Examples:
- Public method signature changed -> parameter boundary tests.
- Nullability annotations changed -> null and default input tests.
- JSON attributes changed -> serialization and deserialization tests.
- New or modified branch logic -> branch and edge-case probes.
- Async method changed -> cancellation, exception, and awaited-result checks.

### Test Template Generator
Responsibilities:
- Generate temporary xUnit, NUnit, or MSTest cases from known patterns.
- Support deterministic generation first.
- Optionally allow controlled LLM-assisted scenario expansion later.

Generation modes:
- `deterministic`: rule-based generation only.
- `ai-assisted`: deterministic generation plus provider-backed scenario expansion.

Rules for `ai-assisted` mode:
- AI assistance must be explicitly enabled in settings.
- Deterministic templates remain the base layer.
- AI-generated output must stay within known template boundaries.
- The system must work end-to-end when AI assistance is disabled.

### AI Provider Abstraction
Responsibilities:
- Provide a stable interface for optional AI-assisted generation.
- Isolate provider-specific configuration, authentication, model selection, and request formatting.
- Allow multiple providers to be added later without changing the core generation pipeline.

Initial provider strategy:
- First supported provider: ChatGPT-compatible models.
- Additional providers can be added later behind the same abstraction.

Provider contract:
- Accept a normalized generation request from the core engine.
- Return structured scenario suggestions, not arbitrary full test projects.
- Respect token, latency, and cost limits defined in settings.
- Return traceable metadata including provider name, model, and request outcome.

Fallback behavior:
- If no provider is configured, the system uses `deterministic` mode only.
- If the configured provider fails, the workflow can fall back to deterministic generation according to policy.
- Pre-commit should default to deterministic-only unless a team explicitly enables AI assistance.

Initial template set:
- Null and empty input handling.
- Boundary and default parameter values.
- Exception mapping and error propagation.
- Serialization round-trip behavior.
- Async cancellation and exception behavior.
- Basic branch coverage probes.

### Runner
Responsibilities:
- Materialize a temporary test project or scratch files.
- Run generated tests.
- Optionally run impacted existing permanent tests.
- Return structured results, logs, and artifacts.

### Results and Promotion Service
Responsibilities:
- Summarize why a test was generated.
- Show which changed symbol triggered it.
- Mark failed temporary tests as candidates for promotion.
- Support promotion into a permanent test project only when approved.

## Local Workflow
The local workflow should support explicit and semi-automatic usage.

Supported triggers:
- Run JiT tests for current file.
- Run JiT tests for current change.
- Optional run on save.
- Optional run before commit.

Recommended default:
- Manual command in Visual Studio.
- Optional pre-commit enforcement enabled per repo.

Local flow:
1. Developer edits a C# file.
2. Extension or CLI detects the changed symbol.
3. Core engine classifies risk.
4. Temporary tests are generated into a scratch location using either deterministic mode or AI-assisted mode.
5. `dotnet test` runs generated tests and a small impacted subset of existing tests.
6. Results are shown in the IDE or terminal.
7. Temporary artifacts are cleaned up unless configured to preserve them for debugging.

AI-assisted local behavior:
- The Visual Studio extension should expose AI assistance as a settings option.
- The user should be able to select `deterministic` or `ai-assisted` generation mode.
- If `ai-assisted` is selected, the user should be able to choose a configured provider and model.
- The UI should clearly show when AI assistance was used for a run.

## Pre-Commit Workflow
The pre-commit hook should call the CLI, not extension-only code.

Goals:
- Keep runtime low.
- Block commits on meaningful failures.
- Stay deterministic.

Pre-commit flow:
1. Read staged changes using `git diff --cached`.
2. Ignore non-code changes.
3. Analyze touched symbols.
4. Generate a small number of temporary tests.
5. Run generated tests and optionally impacted permanent unit tests.
6. Block the commit on failed generated or impacted tests.

Pre-commit constraints:
- Runtime target: 20 to 60 seconds.
- Unit-level scope only.
- No slow external dependencies.
- Hard cap on number of generated tests.
- Fail open during early rollout if generator crashes.
- Fail closed after the workflow has stabilized.
- Default provider policy should be deterministic-only unless the repo config explicitly allows AI assistance.

## Visual Studio Extension Setup Workflow
The Visual Studio extension should provide a first-run setup wizard.

First-run steps:
1. Detect an open C# solution.
2. Validate Visual Studio version and .NET SDK availability.
3. Validate git availability.
4. Detect supported test framework in the solution.
5. Install or validate the companion CLI.
6. Ask the user to choose trigger mode.
7. Ask the user to choose generation mode.
8. If `ai-assisted` is selected, ask the user to choose a provider and model.
9. Ask the user to choose scratch artifact location.
10. Offer to install a repo-local pre-commit hook.
11. Run a dry-run verification.

Recommended trigger modes:
- Manual only.
- Run on save.
- Run before commit.
- Run on build for changed files.

Default trigger mode:
- Manual only.

Recommended default generation mode:
- `deterministic`

Settings UX requirements:
- AI assistance must be opt-in.
- Provider and model selection must be editable after setup.
- The extension should support ChatGPT-compatible models first.
- The settings model should allow more providers to be added later without redesigning the UI.

## Installation Strategy
Use a thin VSIX plus companion CLI.

Reasons:
- The same CLI can be used by extension commands and pre-commit hooks.
- The extension stays focused on UX.
- The engine can be versioned and tested independently.
- Setup remains manageable.

Installation sequence:
1. Install the VSIX.
2. Validate .NET SDK and git.
3. Install or validate the companion CLI.
4. Detect repo-level config if present.
5. Offer repo-local pre-commit hook installation.
6. Run a dry-run validation.

## Repository and Configuration Layout
Suggested files and folders for a C# implementation:
- `src/JitTesting.Core/`
- `src/JitTesting.Cli/`
- `src/JitTesting.VisualStudio/`
- `templates/`
- `.jit-tests/`
- `.config/jit-testing.json`
- `.githooks/pre-commit`

## Extension Settings Model
The extension should own a single settings model that can be edited through the Visual Studio options UI and persisted to a repo-level config file.

Settings groups:
- General settings.
- Generation settings.
- AI provider settings.
- Execution settings.
- Pre-commit settings.
- Debug and diagnostics settings.

### General Settings
- `solutionMode`: `current-solution` or `current-startup-project`
- `triggerMode`: `manual`, `on-save`, `before-commit`, or `on-build`
- `defaultActionScope`: `current-file`, `current-change`, or `staged-change`
- `testFramework`: `xunit`, `nunit`, or `mstest`

### Generation Settings
- `generationMode`: `deterministic` or `ai-assisted`
- `maxGeneratedTestsPerRun`: integer, default `10`
- `includeImpactedPermanentTests`: boolean, default `true`
- `preserveFailedGeneratedTests`: boolean, default `true`
- `cleanupSuccessfulArtifacts`: boolean, default `true`
- `promotionMode`: `manual-only` or `manual-with-template`

### AI Provider Settings
- `providerId`: string, default empty
- `modelId`: string, default empty
- `endpoint`: string, optional
- `platform`: string, default `chatgpt-compatible`
- `authMode`: `api-key`, `oauth`, or `external-token-provider`
- `authReference`: string reference to a secret source or local secure storage key
- `requestTimeoutSeconds`: integer, default `20`
- `maxPromptTokens`: integer, default `4000`
- `maxResponseTokens`: integer, default `2000`
- `allowDeterministicFallback`: boolean, default `true`

### Execution Settings
- `scratchRoot`: path string, default `.jit-tests`
- `timeBudgetSeconds`: integer, default `45`
- `buildBeforeRun`: boolean, default `true`
- `useSolutionWideRestore`: boolean, default `false`
- `verbosity`: `minimal`, `normal`, or `diagnostic`

### Pre-Commit Settings
- `enablePreCommitHook`: boolean, default `false`
- `preCommitGenerationMode`: `deterministic` or `ai-assisted`, default `deterministic`
- `preCommitMaxGeneratedTests`: integer, default `6`
- `preCommitBlockOnGeneratorFailure`: boolean, default `false`

### Debug and Diagnostics Settings
- `writeRunManifest`: boolean, default `true`
- `writeProviderTrace`: boolean, default `false`
- `openResultsToolWindowAfterRun`: boolean, default `true`
- `logDirectory`: path string, optional

### Suggested Repo Config Shape
The repo-level config file should be simple enough for hand editing and stable enough for extension and CLI use.

```json
{
	"general": {
		"solutionMode": "current-solution",
		"triggerMode": "manual",
		"defaultActionScope": "current-change",
		"testFramework": "xunit"
	},
	"generation": {
		"generationMode": "deterministic",
		"maxGeneratedTestsPerRun": 10,
		"includeImpactedPermanentTests": true,
		"preserveFailedGeneratedTests": true,
		"cleanupSuccessfulArtifacts": true,
		"promotionMode": "manual-only"
	},
	"ai": {
		"providerId": "openai",
		"modelId": "gpt-5.4",
		"endpoint": null,
		"platform": "chatgpt-compatible",
		"authMode": "api-key",
		"authReference": "jit-testing.openai.api-key",
		"requestTimeoutSeconds": 20,
		"maxPromptTokens": 4000,
		"maxResponseTokens": 2000,
		"allowDeterministicFallback": true
	},
	"execution": {
		"scratchRoot": ".jit-tests",
		"timeBudgetSeconds": 45,
		"buildBeforeRun": true,
		"useSolutionWideRestore": false,
		"verbosity": "minimal"
	},
	"preCommit": {
		"enablePreCommitHook": false,
		"preCommitGenerationMode": "deterministic",
		"preCommitMaxGeneratedTests": 6,
		"preCommitBlockOnGeneratorFailure": false
	},
	"diagnostics": {
		"writeRunManifest": true,
		"writeProviderTrace": false,
		"openResultsToolWindowAfterRun": true,
		"logDirectory": null
	}
}
```

### Settings Ownership Rules
- The Visual Studio extension is the primary editor for settings.
- The companion CLI must read the same config model.
- Repo-level config should override extension defaults.
- Secret values must not be stored directly in the repo config.
- Provider credentials should be resolved from secure local storage or an external secret source.

## Local Command Flow
The extension should call the companion CLI or shared engine through a small number of explicit command flows.

### Extension Commands
- `Run JiT Tests For Current File`
- `Run JiT Tests For Current Change`
- `Run JiT Tests For Staged Changes`
- `Promote Temporary Test`
- `Open JiT Settings`
- `Enable Pre-Commit Hook`
- `Disable Pre-Commit Hook`

### Command Flow: Run JiT Tests For Current File
1. User invokes the command from the editor context menu, toolbar, or command surface.
2. Extension resolves the active document and owning project.
3. Extension loads merged settings from defaults, repo config, and user overrides.
4. Extension builds a run request with scope `current-file`.
5. Extension invokes the local engine.
6. Engine analyzes the file, maps touched symbols, and builds test intents.
7. Engine generates temporary tests.
8. Engine runs generated tests and selected impacted permanent tests.
9. Extension displays a summary in the tool window and links failures back to source.

### Command Flow: Run JiT Tests For Current Change
1. User invokes the command.
2. Extension gathers unsaved buffer state if needed and aligns it with the current document snapshot.
3. Extension computes the changed span relative to the last saved or tracked state.
4. Extension builds a run request with scope `current-change`.
5. Engine maps changed spans to symbols and classifies risk.
6. Engine generates tests only for impacted symbols.
7. Engine runs the generated test set.
8. Extension renders results and suggested promotion candidates.

### Command Flow: Run JiT Tests For Staged Changes
1. User invokes the command or the pre-commit hook triggers it.
2. Extension or hook requests staged diff analysis.
3. Engine reads `git diff --cached`.
4. Engine filters relevant files and generates tests for staged changes only.
5. Engine runs generated tests within the pre-commit time budget.
6. Extension or hook surfaces pass or fail status.

### Command Flow: Promote Temporary Test
1. User selects a failed or preserved temporary test from the results window.
2. Extension asks for the target permanent test project and test class name if needed.
3. Engine converts the preserved generated test into a cleaned-up permanent template.
4. Extension writes the result into the chosen test project and opens the file for review.

### Run Request Contract
The extension should pass a normalized request into the engine.

Required fields:
- `solutionPath`
- `projectPath`
- `scope`
- `generationMode`
- `testFramework`
- `scratchRoot`
- `timeBudgetSeconds`
- `includeImpactedPermanentTests`

Optional fields:
- `activeDocumentPath`
- `changedSpans`
- `stagedOnly`
- `providerId`
- `modelId`
- `correlationId`

### Run Result Contract
The engine should return a structured result that the extension can render directly.

Required result fields:
- `status`
- `startedAt`
- `durationMs`
- `generationModeUsed`
- `symbolsAnalyzed`
- `testsGenerated`
- `testsExecuted`
- `failedTests`
- `artifactPaths`
- `summary`

Optional result fields:
- `providerTrace`
- `promotionCandidates`
- `diagnosticMessages`
- `fallbackApplied`

### Local UX Requirements For Command Flow
- Every run must show what scope was used.
- Every run must show whether deterministic or AI-assisted generation was used.
- Every generated test should link back to the symbol and risk rule that created it.
- Failures should be clickable from the results tool window.
- The extension should preserve enough artifacts for debugging when a run fails.

## Command Surface
Initial CLI command surface:
- `jit-test analyze --staged`
- `jit-test generate --staged`
- `jit-test run --staged`
- `jit-test pre-commit`
- `jit-test promote <generated-test-id>`

Additional CLI options:
- `--generation-mode deterministic|ai-assisted`
- `--ai-provider <provider>`
- `--ai-model <model>`
- `--no-ai-fallback`

## Initial Implementation Phases

### Phase 0: Foundations
Deliverables:
- Solution structure for core engine, CLI, and VSIX.
- Shared configuration model.
- Scratch artifact strategy.
- Basic logging and diagnostics.

Acceptance criteria:
- CLI can run with a config file.
- VSIX can detect a solution and launch the CLI.
- Scratch directory is created and cleaned correctly.

### Phase 1: Diff and Impact Analysis
Deliverables:
- Git diff reader for staged and branch diffs.
- Roslyn symbol mapping.
- Initial change classification rules.

Acceptance criteria:
- Changed lines can be mapped to symbols.
- Public API and method-level changes can be identified reliably.
- A human-readable analysis report can be produced.

### Phase 2: Deterministic Test Generation
Deliverables:
- Template-driven unit test generation.
- Support for xUnit first.
- Temporary test project generation.

Acceptance criteria:
- The generator can produce compilable temporary tests.
- Generated tests can cover null, boundary, branch, async, and serialization scenarios.
- The generator can explain why each test was created.

### Phase 3: Runner and Pre-Commit Integration
Deliverables:
- Runner orchestration.
- Repo-local git hook installation.
- Fast pre-commit command.

Acceptance criteria:
- `jit-test pre-commit` runs against staged changes.
- Commit is blocked on test failures.
- Local execution stays within agreed time budget for small changes.

### Phase 4: Visual Studio UX
Deliverables:
- Command palette or menu commands.
- Tool window for JiT analysis and results.
- First-run setup wizard.
- Rerun and promotion actions.
- Implemented settings model and config persistence.
- Extension-to-engine run request and run result contracts.

Acceptance criteria:
- Developer can run JiT tests for current file or change from Visual Studio.
- Failures can be traced back to changed symbols.
- Setup is understandable without manual editing of multiple config files.
- The extension can persist, reload, and honor repo-level settings.
- The command flow is stable enough to support manual runs and pre-commit runs through the same engine contract.

### Phase 5: Controlled AI Expansion
Deliverables:
- Optional LLM-assisted scenario expansion.
- Policy controls for when AI generation is allowed.
- Safeguards to keep output within template constraints.

Acceptance criteria:
- AI-generated scenarios remain explainable.
- Generated tests remain deterministic enough for team trust.
- Teams can disable AI generation entirely and still keep the deterministic workflow.

## Rollout Strategy
Use a staged local rollout.

Stage 1:
- Manual CLI use by a small pilot group.

Stage 2:
- Visual Studio extension commands for pilot users.

Stage 3:
- Optional repo-local pre-commit enforcement.

Stage 4:
- Wider team rollout with deterministic generation as default.

Stage 5:
- Optional AI-assisted mode for approved users or repos.

## Key Risks
- Slow local execution will cause developers to bypass the workflow.
- Poor diff-to-symbol mapping will create noisy or irrelevant tests.
- Freeform test generation will reduce trust and reproducibility.
- Automatic promotion of temporary tests will recreate permanent suite bloat.
- Extension-only logic without a shared local engine will fragment behavior between IDE actions and pre-commit.

## Success Metrics
- Time to first useful local result.
- Pre-commit runtime for small changes.
- Percentage of generated tests that compile and run successfully.
- Number of regressions found before local commit.
- Developer adoption and rerun rates.
- Ratio of promoted tests to generated temporary tests.

## Open Questions
- Which test framework should be first-class: xUnit, NUnit, or MSTest?
- Should generated tests be materialized as source files or generated in-memory where possible?
- Which changes should trigger impacted permanent tests in addition to temporary tests?
- Should the extension preserve failed temporary tests by default for debugging?
- What organizational controls are required if LLM expansion is enabled?

## Recommended Starting Point
Start with the smallest viable system:
- xUnit only.
- CLI first.
- Deterministic templates only.
- Pre-commit on staged `.cs` files.
- Visual Studio extension as a thin shell over the CLI.

This approach is the least risky path to a usable JiT testing system and keeps the implementation aligned across local extension actions and pre-commit workflows.