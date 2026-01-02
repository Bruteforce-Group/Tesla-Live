import { Hono } from 'hono';
import { Bindings } from '../index';

const app = new Hono<{ Bindings: Bindings }>();

app.get('/', async (c) => {
  const query = c.req.query('q') || '';
  // TODO: query Vectorize indexes
  return c.json({ query, results: [] });
});

export { app as searchRoutes };
