export async function upsertEmbedding(index: Vectorize, id: string, vector: number[], metadata: any) {
  await index.upsert([{ id, values: vector, metadata }]);
}
