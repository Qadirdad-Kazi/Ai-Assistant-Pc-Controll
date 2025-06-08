// Audio processor for wake word detection
class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.port.onmessage = (event) => {
      // Handle messages from the main thread if needed
    };
    this.bufferSize = 4096;
    this.buffer = new Float32Array(this.bufferSize);
    this.bytesWritten = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    
    // If no input is connected, do nothing
    if (input.length === 0) {
      return true;
    }

    const inputChannel = input[0];
    
    // Simple energy-based voice activity detection
    let sum = 0;
    for (let i = 0; i < inputChannel.length; i++) {
      sum += inputChannel[i] * inputChannel[i];
    }
    const rms = Math.sqrt(sum / inputChannel.length);
    
    // If voice is detected, send a message to the main thread
    if (rms > 0.01) { // Adjust this threshold as needed
      this.port.postMessage({
        type: 'wakeword',
        data: Array.from(inputChannel) // Send a copy of the audio data
      });
    }
    
    // Copy input to output (pass-through)
    const output = outputs[0];
    for (let channel = 0; channel < output.length; channel++) {
      output[channel].set(input[channel]);
    }
    
    return true;
  }
}

// Register the audio processor
registerProcessor('audio-processor', AudioProcessor);
