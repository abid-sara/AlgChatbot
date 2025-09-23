let typingState = {
  isTyping: false,
  answer: '',
  currentIndex: 0,
  messageId: null,
  typingSpeed: 10
};

let typingInterval = null;

self.onmessage = function(e) {
  const { type, data } = e.data;

  switch (type) {
    case 'START_TYPING':
      startTyping(data.answer, data.messageId, data.typingSpeed || 10);
      break;
    
    case 'STOP_TYPING':
      stopTyping();
      break;
    
    case 'GET_STATUS':
      self.postMessage({
        type: 'STATUS_UPDATE',
        data: {
          isTyping: typingState.isTyping,
          currentIndex: typingState.currentIndex,
          messageId: typingState.messageId
        }
      });
      break;
  }
};

function startTyping(answer, messageId, speed) {
  // Stop any existing typing
  stopTyping();
  
  typingState = {
    isTyping: true,
    answer,
    currentIndex: 0,
    messageId,
    typingSpeed: speed
  };

  typeNextCharacter();
}

function typeNextCharacter() {
  if (typingState.currentIndex >= typingState.answer.length) {
    // Typing complete
    self.postMessage({
      type: 'TYPING_COMPLETE',
      data: {
        messageId: typingState.messageId,
        finalContent: typingState.answer
      }
    });
    stopTyping();
    return;
  }

  const newContent = typingState.answer.substring(0, typingState.currentIndex + 1);
  
  self.postMessage({
    type: 'TYPING_UPDATE',
    data: {
      messageId: typingState.messageId,
      content: newContent,
      currentIndex: typingState.currentIndex
    }
  });

  typingState.currentIndex++;
  typingInterval = setTimeout(typeNextCharacter, typingState.typingSpeed);
}

function stopTyping() {
  if (typingInterval) {
    clearTimeout(typingInterval);
    typingInterval = null;
  }
  typingState.isTyping = false;
}