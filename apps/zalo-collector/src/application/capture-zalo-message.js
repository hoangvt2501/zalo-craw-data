"use strict";

async function captureZaloMessageUseCase(message, deps) {
  const { rawMessageRepository, messageMapper } = deps;
  const rawMessage = messageMapper.toRawMessage(message);
  if (!rawMessage || !rawMessage.text) return { status: "ignored" };

  const result = await rawMessageRepository.insertRawMessage(rawMessage);
  return result.inserted
    ? { status: "captured", id: result.id }
    : { status: "duplicate", id: result.id };
}

module.exports = { captureZaloMessageUseCase };
