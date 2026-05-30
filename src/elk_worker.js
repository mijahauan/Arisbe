/**
 * ELK Layout Worker for Arisbe
 *
 * Reads an ELK JSON graph from stdin, runs layout, writes result to stdout.
 * Usage: echo '{"id":"root",...}' | node elk_worker.js
 */
const ELK = require('elkjs');

const elk = new ELK();

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', async () => {
  try {
    const graph = JSON.parse(input);
    const result = await elk.layout(graph);
    // Drain stdout before exit — for large graphs the result can exceed the
    // OS pipe buffer (~64 KB on macOS); a bare process.exit() would truncate.
    process.stdout.write(JSON.stringify(result), () => process.exit(0));
  } catch (err) {
    process.stderr.write(`ELK error: ${err.message}\n`);
    process.exit(1);
  }
});
