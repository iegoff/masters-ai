require('dotenv').config();
const readline = require("readline");
const OpenAI = require("openai");
const args = process.argv.slice(2);
let prompt = args[1];
let apiKey = args[0] || process.env.OPENAI_API_KEY;
const styles = [
  'in the style of a realistic photograph',
  'in the style of a cartoon illustration',
  'in the style of an abstract painting',
  'in the style of a 3D rendering',
  'in the style of pixel art',
  'in the style of a vaporwave aesthetic',
  'in the style of a watercolor painting',
  'in the style of line art sketch',
  'in the style of digital concept art'
];


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
  if (!prompt) {
    prompt = await promptForInput("Prompt: (default: A cute funny cat) ");

    if(!prompt) {
      prompt = 'A funny cat';
    }
  }
  const openai = new OpenAI({
    apiKey: apiKey
  });
  
  try {
    for (let i = 0; i < styles.length; i++) {
      const style = styles[i];
      const combinedPrompt = `${prompt}, ${style}`;
      const image = await openai.images.generate({ 
        model: "dall-e-3", 
        prompt: combinedPrompt 
      });
      console.log(image.data);
    }
  } catch (error) {
    console.error("Error:", error);
  }
}

main();