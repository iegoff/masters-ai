require('dotenv').config();
const { DatabaseSync } = require('node:sqlite');
const readline = require('readline');
const OpenAI = require('openai');
const DATABASE = 'transactions.sqlite';
const db = new DatabaseSync(DATABASE);
const MODEL = 'gpt-4o';
const args = process.argv.slice(2);
let prompt = args[1];
let apiKey = args[0] || process.env.OPENAI_API_KEY;
// Load OpenAI API key
const database_schema_string = `
Table: transactions
Columns: transaction_id, prop_group, is_offplan, prop_usage, prop_area, prop_type, prop_sb_type, prop_price, prop_area_sqf, prop_rooms, project_name 
All colums are of type TEXT
Example row: 102-1-2025,	Sales Off-Plan,	Residential,	Wadi Al Safa 4,	Unit,	Flat,	1421000,	68.67, 1 B/R, Lacina
`

const tools = [{
  type: "function",
  function: {
    name: "ask_database",
    description: "Use this function to answer user questions about data. Output should be a fully formed SQL query.",
    parameters: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: `
                            SQL query extracting info to answer the user's question.
                            SQL should be written using this database schema:
                            ${database_schema_string}
                            The query should be returned in plain text, not in JSON.
                            `,
        }
      },
      required: ["query"],
      additionalProperties: false
    }
  }
}];
// Query database
function askDatabase(query) {
  const aiquery = db.prepare(query);
  // Execute the prepared statement and log the result set.
  return aiquery.all();
}


// Generate chat completion
async function chatCompletionRequest(messages, tools, apiKey) {
  try {
    const openai = new OpenAI({
      apiKey: apiKey
    });
    const response = await openai.chat.completions.create({
      model: MODEL,
      messages,
      tools,
    });
    return response;
  } catch (error) {
    console.error(`Error in ChatCompletion: ${error.message}`);
  }
}
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
// Main function
async function main() {
  if (!apiKey) {
    apiKey = await promptForInput("Please enter your OpenAI API key:\n");
  }
  if (!prompt) {
    prompt = await promptForInput("Write the Prompt: (default: What is the total number of units that cost more than 1m?)\n");

    if (!prompt) {
      prompt = "What is the total number of units that cost more than 1m?";
    }
  }


  const messages = [
    {
      role: "system", content: `You are DatabaseGPT, a helpful assistant who gets answers to user questions from the Database 
      Provide as many details as possible to your users 
      Begin!` },
    { role: "user", content: prompt },
  ];



  const response = await chatCompletionRequest(messages, tools, apiKey);
  if (response && response.choices) {
    const firstChoice = response.choices[0];
    if (firstChoice.message.tool_calls) {
      const functionCall = firstChoice.message.tool_calls[0].function;
      if (functionCall.name === "ask_database") {
        const query = JSON.parse(functionCall.arguments).query;
        console.log(`Generated query: ${query}`);

        try {
          const results = await askDatabase(query);
          console.log("Results:", results);
        } catch (err) {
          console.error(err);
        }
      }
    } else {
      console.log("Response:", firstChoice.message.content);
    }
  }
}

main();