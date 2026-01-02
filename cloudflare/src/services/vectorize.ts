export async function upsertEmbedding(
  index: Vectorize,
  id: string,
  vector: number[],
  metadata: Record<string, VectorizeVectorMetadata>,
) {
  await index.upsert([{ id, values: vector, metadata }]);
}
