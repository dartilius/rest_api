import assert from 'node:assert/strict';
import test from 'node:test';
import { TextEncoder } from 'node:util';
import {
  exportSPKI,
  generateKeyPair,
  SignJWT,
} from 'jose';
import {
  DjangoJwtVerifier,
  type DjangoJwtConfig,
  InvalidDjangoJwtError,
} from '../src/auth/django-jwt-verifier.service';

const issuer = 'rmc-django';
const audience = 'rmc-site-api';

async function makeRs256Verifier(): Promise<DjangoJwtVerifier> {
  const pair = await generateKeyPair('RS256');
  const config: DjangoJwtConfig = {
    issuer,
    audience,
    publicKeyPem: await exportSPKI(pair.publicKey),
  };
  const verifier = new DjangoJwtVerifier(config);
  const token = await new SignJWT({ token_type: 'access', role: 'manager' })
    .setProtectedHeader({ alg: 'RS256' })
    .setSubject('user-1')
    .setIssuer(issuer)
    .setAudience(audience)
    .setIssuedAt()
    .setExpirationTime('1h')
    .sign(pair.privateKey);
  return Object.assign(verifier, { testToken: token });
}

test('verifies a Django RS256 access token and exposes permitted claims', async () => {
  const verifier = await makeRs256Verifier() as DjangoJwtVerifier & { testToken: string };
  assert.deepEqual(await verifier.verifyAccessToken(verifier.testToken), {
    id: 'user-1',
    role: 'manager',
    tokenVersion: 'rs256',
  });
});

test('rejects an RS256 token for a different audience', async () => {
  const pair = await generateKeyPair('RS256');
  const verifier = new DjangoJwtVerifier({
    issuer,
    audience,
    publicKeyPem: await exportSPKI(pair.publicKey),
  });
  const token = await new SignJWT({ token_type: 'access' })
    .setProtectedHeader({ alg: 'RS256' })
    .setSubject('user-1')
    .setIssuer(issuer)
    .setAudience('another-api')
    .setIssuedAt()
    .setExpirationTime('1h')
    .sign(pair.privateKey);

  await assert.rejects(verifier.verifyAccessToken(token), InvalidDjangoJwtError);
});

test('accepts a legacy HS256 access token only before the configured deadline', async () => {
  const secret = 'old-django-secret';
  const token = await new SignJWT({ token_type: 'access', user_id: 'legacy-user' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('1h')
    .sign(new TextEncoder().encode(secret));
  const verifier = new DjangoJwtVerifier({
    issuer,
    audience,
    legacySecret: secret,
    legacyAcceptUntil: new Date(Date.now() + 60_000),
  });

  assert.deepEqual(await verifier.verifyAccessToken(token), {
    id: 'legacy-user',
    tokenVersion: 'legacy-hs256',
  });
});
