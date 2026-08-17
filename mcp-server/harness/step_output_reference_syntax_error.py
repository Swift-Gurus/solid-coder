"""Defines an invalid authored step-output expression error."""


"""
solid-name: StepOutputReferenceSyntaxError
solid-category: error
solid-spec: [SPEC-030, SPEC-037]
solid-description: Signals that an authored expression does not match the supported local step-output reference grammar.
"""
class StepOutputReferenceSyntaxError(ValueError):
    pass
