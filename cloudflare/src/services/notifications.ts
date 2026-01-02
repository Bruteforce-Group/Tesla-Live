export async function sendNotification(queue: Queue, payload: any) {
  await queue.send(payload);
}
