require('dotenv').config();
const readline = require("readline");
const OpenAI = require("openai");
const fs = require('node:fs');
const args = process.argv.slice(2);
let transcript = args[1];
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
  if (!transcript) {
    transcript = await promptForInput("Please provide transcript: (default: lesson-1-transcript.txt) ");

    if(!transcript) {
      transcript = 'lesson-1-transcript.txt';
    }
  }
  const data = fs.readFileSync(transcript, 'utf8');
  const openai = new OpenAI({
    apiKey: apiKey
  });
  
  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-4o",
      temperature: 0.2,
      stream: true,
      messages: [
        { role: "system", content: 'You are an expert blog writer. When given transcript, create a well-structured blog post.' },
        {
          role: 'user',
          content: `
            Transcript: ${data}
            
            Please write a detailed blog post using Transcript and provide some quotes.
          `,
        },
      ],
    });

    for await (const chunk of completion) {
      process.stdout.write(chunk.choices[0]?.delta?.content || "");
  }
  } catch (error) {
    console.error("Error:", error);
  }
}

main();