# Count-based Outline Generation Design

## Goal

Allow the user to generate only the requested number of outline files while using character JSON profiles as the default character pool.

## Command Interface

- `python3 generate_outlines.py 10` generates `001화.txt` through `010화.txt`.
- The count is a required positive integer.
- `python3 generate_outlines.py 10 --character 윤수빈` limits generation to that character.
- Invalid counts and character names exit with a clear command-line error.

## Character Selection

- Without `--character`, only characters that have a matching `profiles/<name>.json` file participate.
- Profiled characters are used in `CHARACTER_ORDER` order and rotate when more than one profile exists.
- With the current single JSON profile, every requested outline uses 윤수빈.
- With `--character`, the named character must have both a character text file and a JSON profile.

## Output Behavior

- Generation starts at episode 1 and writes exactly the requested range for the current run.
- Existing files inside that range are overwritten.
- Existing files after the requested range are preserved to avoid deleting user work.
- The completion message reports the number and range generated.

## Structure

- Argument parsing is separated into `parse_args`.
- Profile-backed character filtering is separated from file writing.
- A generation function accepts the count and optional character name so tests can exercise behavior without invoking a subprocess.
- Existing scene selection and outline rendering remain unchanged.

## Tests

- Parsing accepts a positive requested count and optional character.
- Invalid counts are rejected.
- The default pool contains only JSON-profiled characters.
- A single JSON-profiled character is reused for every requested episode.
- Generation writes only the requested episode range and preserves later files.
- An unknown or non-profiled character is rejected clearly.
