export default {
  async queue(batch: MessageBatch) {
    for (const msg of batch.messages) {
      // TODO: process video jobs
      console.log('Video message', msg.body);
    }
  },
};
