const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');

// Define file paths (adjust as needed)
const JSON_FILES = {
  "index.html": path.join(__dirname, "../output/5html_converted_content.json")
};

const QA_JSON_FILE = path.join(__dirname, "../output/6email_feedback.json");

// Helper functions for JSON files
function loadRecords() {
  const jsonFile = JSON_FILES["index.html"];
  console.log("Loading JSON from:", jsonFile);
  if (fs.existsSync(jsonFile)) {
    try {
      return JSON.parse(fs.readFileSync(jsonFile, 'utf-8'));
    } catch (err) {
      console.error("Error parsing JSON:", err);
      return [];
    }
  }
  return [];
}

function saveRecords(records) {
  const jsonFile = JSON_FILES["index.html"];
  fs.writeFileSync(jsonFile, JSON.stringify(records, null, 4), 'utf-8');
}

function loadFeedbackRecords() {
  if (fs.existsSync(QA_JSON_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(QA_JSON_FILE, 'utf-8'));
    } catch (err) {
      console.error("Error parsing JSON:", err);
      return [];
    }
  }
  return [];
}

function saveFeedbackRecords(records) {
  fs.writeFileSync(QA_JSON_FILE, JSON.stringify(records, null, 4), 'utf-8');
}

// Serve static files from the ../output directory
function serveOutputFile(filename) {
  const filePath = path.join(__dirname, "../output", filename);
  if (fs.existsSync(filePath)) {
    const ext = path.extname(filePath).toLowerCase();
    let contentType = 'application/octet-stream';
    if (ext === '.html') contentType = 'text/html';
    else if (ext === '.json') contentType = 'application/json';
    else if (ext === '.wav') contentType = 'audio/wav';
    else if (ext === '.txt') contentType = 'text/plain';

    const fileContent = fs.readFileSync(filePath);
    return {
      statusCode: 200,
      headers: { 'Content-Type': contentType },
      body: fileContent.toString('base64'),
      isBase64Encoded: true,
    };
  } else {
    return { statusCode: 404, body: "File not found" };
  }
}

// The Netlify serverless function handler
exports.handler = async (event, context) => {
  const method = event.httpMethod;
  const url = event.path;
  console.log(`Received request: ${method} ${url}`);

  // Route: Serve files from /output/*
  if (url.startsWith('/output/')) {
    const filename = url.replace('/output/', '');
    return serveOutputFile(filename);
  }

  // Route: Index ("/" or "/index.html")
  if (url === '/' || url === '/index.html') {
    const records = loadRecords();
    // For simplicity, we build a minimal HTML page displaying the JSON records.
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <title>Index</title>
        </head>
        <body>
          <h1>Records</h1>
          <pre>${JSON.stringify(records, null, 4)}</pre>
        </body>
      </html>
    `;
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'text/html' },
      body: htmlContent,
    };
  }

  // Route: Update a record ("/update_record")
  if (url === '/update_record' && method === 'POST') {
    let data;
    try {
      data = JSON.parse(event.body);
    } catch (err) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "Invalid JSON." }),
      };
    }

    const recordIndex = data.index;
    const updatedRecord = data.record;
    if (updatedRecord === undefined) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "No record provided." }),
      };
    }

    const idx = parseInt(recordIndex, 10);
    if (isNaN(idx)) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "Invalid record index." }),
      };
    }

    const records = loadRecords();
    if (idx < 0 || idx >= records.length) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "Record index out of range." }),
      };
    }

    records[idx] = updatedRecord;
    saveRecords(records);
    return {
      statusCode: 200,
      body: JSON.stringify({ status: "success", message: "Record updated successfully." }),
    };
  }

  // Route: Update feedback ("/update_feedback")
  if (url === '/update_feedback' && method === 'POST') {
    let data;
    try {
      data = JSON.parse(event.body);
    } catch (err) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "Invalid JSON." }),
      };
    }

    const recordIndex = data.index;
    const updatedRecord = data.record;
    if (updatedRecord === undefined) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "No record provided." }),
      };
    }

    const idx = parseInt(recordIndex, 10);
    if (isNaN(idx)) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "Invalid record index." }),
      };
    }

    const records = loadFeedbackRecords();
    if (idx < 0 || idx >= records.length) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "Record index out of range." }),
      };
    }

    records[idx] = updatedRecord;
    saveFeedbackRecords(records);
    return {
      statusCode: 200,
      body: JSON.stringify({ status: "success", message: "QA feedback updated successfully." }),
    };
  }

  // Route: Synthesize speech ("/synthesizeSpeech")
  if (url === '/synthesizeSpeech' && method === 'POST') {
    let data;
    try {
      data = JSON.parse(event.body);
    } catch (err) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", message: "Invalid JSON." }),
      };
    }

    const text = data.text || "Hello from Azure TTS!";
    try {
      await new Promise((resolve, reject) => {
        execFile('node', ['azure-speech.js', text], { cwd: __dirname }, (error, stdout, stderr) => {
          if (error) {
            console.error("Error executing azure-speech.js:", error);
            reject(error);
          } else {
            resolve();
          }
        });
      });
      return {
        statusCode: 200,
        body: JSON.stringify({
          status: "success",
          message: "Speech synthesized",
          audioUrl: "/output/speech.wav"
        }),
      };
    } catch (err) {
      return {
        statusCode: 500,
        body: JSON.stringify({ status: "error", message: err.toString() }),
      };
    }
  }

  // No matching route found
  return {
    statusCode: 404,
    body: "Not Found",
  };
};
