### Research OSCAL Pydantic Library Evaluation

**Deps:** None

Research ticket — produces a written recommendation, no code.

- Survey available OSCAL Python libraries, starting with [oscal-pydantic](https://github.com/RS-Credentive/oscal-pydantic/tree/oscal-pydantic-v2)
- Evaluate each candidate against these criteria:
  - **OSCAL version coverage:** Which OSCAL models are supported (catalog, profile, SSP, component-definition)?
  - **Pydantic compatibility:** Must support Pydantic v2
  - **Python compatibility:** Must work with Python 3.14+
  - **Maturity:** Commit activity, number of maintainers, open issues, test coverage
  - **API quality:** Can models be used directly or do they need wrapping/adaptation?
  - **Scope fit:** Do we need full OSCAL parsing or just the subset relevant to policies, standards, and statements?
  - **License:** Must be compatible with the project
- Evaluate the alternative: rolling our own minimal Pydantic models covering only the OSCAL subset we need
- Write a recommendation document to `docs/decisions/` with findings and a clear recommendation (use library X, or roll our own because Y)

**Done:** A written recommendation exists in `docs/decisions/` that covers all evaluation criteria, states a clear recommendation, and provides sufficient rationale for the governance model design in T9–T11.
