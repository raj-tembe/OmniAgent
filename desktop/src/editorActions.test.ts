import { test } from "node:test";
import assert from "node:assert/strict";
import { composeActionPrompt, EDITOR_ACTIONS } from "./editorActions.ts";

test("explain action includes the file path and content", () => {
  const prompt = composeActionPrompt("explain", "src/main.py", "print('hi')\n");

  assert.match(prompt, /Explain what the following file does/);
  assert.match(prompt, /src\/main\.py/);
  assert.match(prompt, /print\('hi'\)/);
});

test("fix action asks for bugs, lint issues, and type errors", () => {
  const prompt = composeActionPrompt("fix", "app.py", "x = 1\n");

  assert.match(prompt, /bugs, lint issues, and type errors/);
  assert.match(prompt, /app\.py/);
});

test("test action asks for unit tests", () => {
  const prompt = composeActionPrompt("test", "utils.py", "def add(a, b): return a + b\n");

  assert.match(prompt, /Write unit tests/);
  assert.match(prompt, /utils\.py/);
});

test("content is wrapped in a code fence", () => {
  const prompt = composeActionPrompt("explain", "a.py", "x = 1\n");
  const fenceCount = (prompt.match(/```/g) || []).length;

  assert.equal(fenceCount, 2);
});

test("does not double up trailing newlines before the closing fence", () => {
  const withNewline = composeActionPrompt("explain", "a.py", "x = 1\n");
  const withoutNewline = composeActionPrompt("explain", "a.py", "x = 1");

  // both should have exactly one newline right before the closing fence
  assert.match(withNewline, /x = 1\n```$/);
  assert.match(withoutNewline, /x = 1\n```$/);
});

test("EDITOR_ACTIONS lists exactly the three supported actions", () => {
  const ids = EDITOR_ACTIONS.map((a) => a.id);
  assert.deepEqual(ids.sort(), ["explain", "fix", "test"]);
});

test("empty file content still produces a well-formed prompt", () => {
  const prompt = composeActionPrompt("explain", "empty.py", "");
  assert.match(prompt, /```\n```$/);
});
