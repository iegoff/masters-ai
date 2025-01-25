const readline = require("readline");
const { spawn } = require("child_process");
const fs = require('node:fs');
const args = process.argv.slice(2);
let audio = args[0];


function promptForInput(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}
async function main() {
  if (!audio) {
    audio = await promptForInput("Please provide recording: (default: rec.mp3) ");

    if (!audio) {
      audio = 'rec.mp3';
    }
  }


  try {
    return new Promise((resolve, reject) => {
      const child = spawn("whisper", [
        audio,
        "--model", "base",
        "--output_format", "txt",
        "--language", "en"
      ]);
      child.stdout.on("data", (data) => {
        console.log(`STDOUT: ${data}`);
      });
      child.stderr.on("data", (data) => {
        console.error(`STDERR: ${data}`);
      });
      child.on("close", (code) => {
        if (code !== 0) {
          reject(new Error(`Whisper process exited with code ${code}`));
        }
      });
    });
  } catch (error) {
    console.error("Error:", error);
  }
}

main();