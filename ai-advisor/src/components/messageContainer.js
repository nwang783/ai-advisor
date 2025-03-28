import React from 'react';
import Markdown from 'markdown-to-jsx';

const MessageContainer = ({ message }) => {
  return (
    <div className="message-container">
      <h2>Reasoning</h2>
      <Markdown>{message}</Markdown>
    </div>
  );
};

export default MessageContainer;
