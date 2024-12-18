const functions = require("firebase-functions");
const { OpenAI } = require("openai");
const cors = require("cors"); 

// Load environment variables
const openai = new OpenAI({
    apiKey: "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",
  });

// CORS middleware
const corsHandler = cors({ origin: true }); // This allows all origins to access the function

// === Helper Function to Wait for Run Completion ===
async function waitForRunCompletion(threadId, assistantId, userMessage) {
  try {
    // Step 1: Add user message to the thread
    console.log(`User Message in helper function: ${userMessage}`)
    await openai.beta.threads.messages.create(threadId, {
      role: "user",
      content: userMessage,
    });

    // Step 2: Start the assistant run
    const run = await openai.beta.threads.runs.create(threadId, {
      assistant_id: assistantId,
    });

    const runId = run.id;

    // Step 3: Poll the run status until completion
    while (true) {
      const updatedRun = await openai.beta.threads.runs.retrieve(threadId, runId);
      if (updatedRun.completed_at) {
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 2000)); // Sleep 2 seconds
    }

    // Step 4: Retrieve assistant response
    const messages = await openai.beta.threads.messages.list(threadId);
    const lastMessage = messages.data[0]; // Latest assistant response
    const responseText = lastMessage.content[0]?.text?.value;

    return responseText || "No response from assistant.";
  } catch (error) {
    console.error("Error during OpenAI interaction:", error);
    throw new Error("Failed to fetch assistant response.");
  }
}

// === Firebase HTTP Function ===
exports.csAdvisorChat = functions.https.onRequest({
  cors: true, // Enable CORS for all origins
  methods: ['POST'], // Explicitly specify allowed methods
}, async (req, res) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    res.set('Access-Control-Allow-Origin', '*');
    res.set('Access-Control-Allow-Methods', 'POST');
    res.set('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(204).send('');
  }

  // Ensure only POST requests are processed
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    // Set CORS headers for the actual response
    res.set('Access-Control-Allow-Origin', '*');

    // Parse the request body
    console.log(`Parsed body: ${JSON.stringify(req.body)}`);
    let { user_message, thread_id } = req.body.data || {};
    console.log(`User message in main function: ${user_message}`);
    const assistantId = "asst_GP623DT51AwCa5jYxfauA7aP";

    if (!user_message) {
      user_message = "Tell the user who you are";
      console.log("User message is blank");
    }

    let threadId = thread_id;

    if (!threadId) {
      const thread = await openai.beta.threads.create();
      threadId = thread.id;
      console.log(`New thread created: ${threadId}`);
    } else {
      console.log(`Using existing thread: ${threadId}`);
    }

    const assistantResponse = await waitForRunCompletion(threadId, assistantId, user_message);
    console.log(`Assistant Response: ${assistantResponse}`);

    // Log the response structure
    const responseBody = {
      response: assistantResponse,
      thread_id: threadId,
    };

    console.log(`Response body being sent: ${JSON.stringify(responseBody)}`);

    // Send a proper HTTP response
    return res.status(200).json({
      status: "success",
      data: {
        response: assistantResponse,
        thread_id: threadId,
      },
    });
  } catch (error) {
    console.error("Error:", error);
    return res.status(500).json({ error: "Internal server error" });
  }
});
