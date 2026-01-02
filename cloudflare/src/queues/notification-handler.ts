export default {
  async queue(batch: MessageBatch) {
    for (const msg of batch.messages) {
      // TODO: deliver notifications
      console.log('Notification message', msg.body);
    }
  },
};
