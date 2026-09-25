import { config } from 'dotenv';
import { resolve } from 'node:path';

// Nest CLI may run the compiled app with a workspace-root cwd. Resolve from
// this source/dist file instead, so `.env` always means `nest-backend/.env`.
config({ path: resolve(__dirname, '..', '..', '.env'), quiet: true });
