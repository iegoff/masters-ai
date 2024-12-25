require('dotenv').config();
const readline = require("readline");
const OpenAI = require("openai");
const fs = require('node:fs');
const args = process.argv.slice(2);
let audio = args[1];
let apiKey = args[0] || process.env.OPENAI_API_KEY;


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
  if (!apiKey) {
    apiKey = await promptForInput("Please enter your OpenAI API key: ");
  }
  if (!audio) {
    audio = await promptForInput("Please provide recording: (default: rec.mp3) ");

    if(!audio) {
      audio = 'rec.mp3';
    }
  }
  const openai = new OpenAI({
    apiKey: apiKey
  });
  
  try {
    const transcription = await openai.audio.transcriptions.create({
      file: fs.createReadStream(audio),
      model: "whisper-1",
      language: "en",
      temperature: 0,
    });
  
    console.log(transcription.text);

  } catch (error) {
    console.error("Error:", error);
  }
}

main();