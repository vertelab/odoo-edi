# -*- coding: utf-8 -*-
"""Provides helper functions."""

import regex

from edifact.exceptions import MissingSegmentAtPositionError


def separate_segments(src_string, segment_terminator='\'', release_character='?'):
    """Separate the segments in an EDIFACT message string."""
    separator_pattern = r'(?<!\{rc}){st}'.format(st=segment_terminator, rc=release_character)
    raw_segments = regex.split(separator_pattern, src_string)
    return [raw_segment.strip().replace('\\n', '') + segment_terminator for raw_segment in raw_segments if not raw_segment == '']


def separate_components(src_string, data_element_separator='+', component_data_element_separator=':', segment_terminator='\'', release_character='?'):
    """Separate the components in an EDIFACT segment string."""
    output = []

    if src_string[-1] == '\'':
        src_string = src_string[0:-1]

    simple_separator_pattern = r'(?<!\{rc})\{des}'.format(des=data_element_separator, rc=release_character)
    simple_data_elements = regex.split(simple_separator_pattern, src_string)

    component_separator_pattern = r'(?<!\{rc})\{cdes}'.format(cdes=component_data_element_separator, rc=release_character)
    for simple_data_element in simple_data_elements:
        components = regex.split(component_separator_pattern, simple_data_element)
        if len(components) == 1:
            output.append(simple_data_element)
        else:
            output.append(components)

    return output


def validate_anchor_segments(segments):
    """Very basic validation of segments, making sure UNH, BGM and UNT exist and are in the right place."""
    if not (segments[0][0] == 'UNH' or segments[1][0] == 'UNH'):
        raise MissingSegmentAtPositionError('UNH')
    if not (segments[1][0] == 'BGM' or segments[2][0] == 'BGM'):
        raise MissingSegmentAtPositionError('BGM')
    if not segments[-1][0] == 'UNT':
        raise MissingSegmentAtPositionError('UNT')
