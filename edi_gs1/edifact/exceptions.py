class InvalidEdifact(ValueError):
	"""EDIFACT data is invalid."""


class MissingSegmentAtPositionError(InvalidEdifact):
	"""Segment is mandatory at position but could not be found. Missing or misplaced."""
