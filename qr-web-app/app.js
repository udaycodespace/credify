const startScanBtn = document.getElementById('startScanBtn');
const stopScanBtn = document.getElementById('stopScanBtn');
const qrFile = document.getElementById('qrFile');
const qrLinkInput = document.getElementById('qrLinkInput');
const verifyLinkBtn = document.getElementById('verifyLinkBtn');
const camera = document.getElementById('camera');
const scanCanvas = document.getElementById('scanCanvas');
const uploadCanvas = document.getElementById('uploadCanvas');
const statusBadge = document.getElementById('statusBadge');
const resultCard = document.getElementById('resultCard');

let activeVideoTrack = null;
const codeReader = new ZXing.BrowserQRCodeReader();

const TRUSTED_HOSTS = ['localhost', '127.0.0.1', 'www.udaycodespace.com', 'udaycodespace.github.io'];
const ISSUER_REGISTRY_PATH = './trusted_issuers.json';
let trustedIssuers = {};
const CONSUMED_QR_STORE_KEY = 'credify_consumed_qr_tokens_v1';

function decodeBase64Url(str) {
  const padded = str + '='.repeat((4 - (str.length % 4)) % 4);
  const b64 = padded.replace(/-/g, '+').replace(/_/g, '/');
  return atob(b64);
}

function bytesFromBase64Url(str) {
  const raw = decodeBase64Url(str);
  return Uint8Array.from(raw, c => c.charCodeAt(0));
}

async function decodeQdPayload(qd) {
  const bytes = bytesFromBase64Url(qd);
  const decoder = new TextDecoder('utf-8');

  // Old format support: qd contained plain JSON bytes.
  try {
    const asText = decoder.decode(bytes);
    const parsed = JSON.parse(asText);
    return { payloadText: asText, parsed };
  } catch {
    // Continue to gzip decode path.
  }

  // New format: qd is gzip-compressed JSON.
  if (typeof DecompressionStream !== 'function') {
    if (typeof pako !== 'undefined' && pako.ungzip) {
      const decompressed = pako.ungzip(bytes, { to: 'string' });
      const parsed = JSON.parse(decompressed);
      return { payloadText: decompressed, parsed };
    }
    throw new Error('Gzip QR payload is not supported by this browser');
  }

  const ds = new DecompressionStream('gzip');
  const stream = new Blob([bytes]).stream().pipeThrough(ds);
  const decompressed = await new Response(stream).arrayBuffer();
  const payloadText = decoder.decode(new Uint8Array(decompressed));
  const parsed = JSON.parse(payloadText);
  return { payloadText, parsed };
}

function toUtf8Bytes(text) {
  return new TextEncoder().encode(text);
}

function escapeHtml(text) {
  return String(text ?? 'N/A')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function pemToArrayBuffer(pem) {
  const b64 = pem.replace(/-----BEGIN PUBLIC KEY-----|-----END PUBLIC KEY-----|\s+/g, '');
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

async function sha256Hex(text) {
  const digest = await crypto.subtle.digest('SHA-256', toUtf8Bytes(text));
  return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('');
}

function getConsumedTokens() {
  try {
    const raw = localStorage.getItem(CONSUMED_QR_STORE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function setConsumedTokens(map) {
  try {
    localStorage.setItem(CONSUMED_QR_STORE_KEY, JSON.stringify(map));
  } catch {
    // ignore storage errors
  }
}

async function qrTokenFingerprint(qk) {
  return sha256Hex(String(qk || ''));
}

async function isQrAlreadyConsumed(qk) {
  const fp = await qrTokenFingerprint(qk);
  const map = getConsumedTokens();
  return !!map[fp];
}

async function markQrConsumed(qk, cid) {
  const fp = await qrTokenFingerprint(qk);
  const map = getConsumedTokens();
  map[fp] = {
    consumedAt: new Date().toISOString(),
    cid: cid || null,
  };
  setConsumedTokens(map);
}

async function loadIssuerRegistry() {
  try {
    const resp = await fetch(ISSUER_REGISTRY_PATH, { cache: 'no-cache' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    trustedIssuers = data.issuers || {};
    return true;
  } catch {
    trustedIssuers = {};
    return false;
  }
}

async function verifyJwsToken(qk, payloadText, expectedCid) {
  const parts = String(qk || '').split('.');
  if (parts.length !== 3) {
    return { ok: false, mode: 'legacy', reason: 'Legacy token format (no offline public-key verify).' };
  }

  try {
    const [headerB64, payloadB64, signatureB64] = parts;
    const header = JSON.parse(decodeBase64Url(headerB64));
    const payload = JSON.parse(decodeBase64Url(payloadB64));
    const signingInput = `${headerB64}.${payloadB64}`;
    const issuerId = payload.iss;
    const issuer = trustedIssuers[issuerId];

    if (!issuer || !issuer.publicKeyPem) {
      return { ok: false, mode: 'offline', reason: `Unknown issuer: ${issuerId || 'missing'}`, payload };
    }

    const publicKey = await crypto.subtle.importKey(
      'spki',
      pemToArrayBuffer(issuer.publicKeyPem),
      { name: 'RSA-PSS', hash: 'SHA-256' },
      false,
      ['verify']
    );

    const isSignatureValid = await crypto.subtle.verify(
      { name: 'RSA-PSS', saltLength: 32 },
      publicKey,
      bytesFromBase64Url(signatureB64),
      toUtf8Bytes(signingInput)
    );

    if (!isSignatureValid) {
      return { ok: false, mode: 'offline', reason: 'Signature mismatch', payload, issuerId };
    }

    if (expectedCid && payload.cid && String(payload.cid) !== String(expectedCid)) {
      return { ok: false, mode: 'offline', reason: 'Credential ID mismatch', payload, issuerId };
    }

    if (payload.pd && payloadText) {
      const qdHash = await sha256Hex(payloadText);
      if (qdHash !== payload.pd) {
        return { ok: false, mode: 'offline', reason: 'Payload digest mismatch (QR tampered)', payload, issuerId };
      }
    }

    return {
      ok: true,
      mode: 'offline',
      reason: 'Offline signature validation passed',
      payload,
      issuerId,
      issuerName: issuer.name || issuerId,
      algorithm: header.alg || issuer.algorithm || 'PS256'
    };
  } catch (err) {
    return { ok: false, mode: 'offline', reason: `Token parse/verify error: ${String(err)}` };
  }
}

function setStatus(type, text) {
  statusBadge.className = `badge ${type}`;
  statusBadge.textContent = text;
}

function renderCardHtml(html) {
  resultCard.innerHTML = html;
}

function parseQrPayload(payload) {
  const text = String(payload || '').trim();
  if (!text) return { ok: false, reason: 'Empty QR payload' };

  try {
    const url = new URL(text);
    if (!['http:', 'https:'].includes(url.protocol)) {
      return { ok: false, reason: 'Unsupported QR URL protocol' };
    }
    const hostTrusted = TRUSTED_HOSTS.includes(url.hostname.toLowerCase());
    const id = url.searchParams.get('id');
    const qk = url.searchParams.get('qk');
    const qd = url.searchParams.get('qd');

    if (!id || !qk || !qd) {
      return { ok: false, reason: 'Missing id/qk/qd in QR' };
    }

    return {
      ok: true,
      credentialId: id,
      qk,
      qd,
      source: `url:${url.hostname}${hostTrusted ? '' : ' (untrusted-host)'}`,
      hostTrusted
    };
  } catch {
    return { ok: false, reason: 'QR does not contain a valid verify URL' };
  }
}

function renderDecodedSecret(decoded, sourceTag, offlineCheck) {
  const offlineOk = !!(offlineCheck && offlineCheck.ok);
  setStatus(offlineOk ? 'real' : 'fake', offlineOk ? 'VALID' : 'INVALID');
  renderCardHtml(`
    <div class="${offlineOk ? 'ok' : 'fail'}" style="font-size: 1.1rem; margin-bottom: 8px;">
      ${offlineOk ? 'Credential Verified ✅' : 'Credential Invalid ❌'}
    </div>
    <div>${escapeHtml(offlineCheck?.reason || '')}</div>
    <h3 style="margin:12px 0 6px; color:#22d3ee;">Student Information</h3>
    <div class="info-grid">
      <div class="k">Name</div><div class="v">${escapeHtml(decoded.name)}</div>
      <div class="k">Student Id</div><div class="v">${escapeHtml(decoded.studentId)}</div>
      <div class="k">Degree</div><div class="v">${escapeHtml(decoded.degree)}</div>
      <div class="k">Department</div><div class="v">${escapeHtml(decoded.department)}</div>
      <div class="k">Student Status</div><div class="v">${escapeHtml(decoded.studentStatus)}</div>
      <div class="k">College</div><div class="v">${escapeHtml(decoded.college)}</div>
      <div class="k">University</div><div class="v">${escapeHtml(decoded.university)}</div>
      <div class="k">CGPA</div><div class="v">${escapeHtml(decoded.cgpa ?? 'N/A')}</div>
      <div class="k">Graduation Year</div><div class="v">${escapeHtml(decoded.graduationYear)}</div>
      <div class="k">Batch</div><div class="v">${escapeHtml(decoded.batch)}</div>
      <div class="k">Conduct</div><div class="v">${escapeHtml(decoded.conduct)}</div>
      <div class="k">Backlog Count</div><div class="v">${escapeHtml(decoded.backlogCount ?? '0')}</div>
      <div class="k">Courses</div><div class="v">${escapeHtml(Array.isArray(decoded.courses) && decoded.courses.length ? decoded.courses.join(', ') : 'N/A')}</div>
      <div class="k">Backlogs</div><div class="v">${escapeHtml(Array.isArray(decoded.backlogs) && decoded.backlogs.length ? decoded.backlogs.join(', ') : 'N/A')}</div>
      <div class="k">Issue Date</div><div class="v">${escapeHtml(decoded.issueDate)}</div>
      <div class="k">Semester</div><div class="v">${escapeHtml(decoded.semester)}</div>
      <div class="k">Year</div><div class="v">${escapeHtml(decoded.year)}</div>
      <div class="k">Section</div><div class="v">${escapeHtml(decoded.section)}</div>
      <div class="k">Credential ID</div><div class="v">${escapeHtml(decoded.cid)}</div>
      <div class="k">IPFS CID</div><div class="v">${escapeHtml(decoded.ipfsCid)}</div>
    </div>
    <div style="margin-top:8px; color:#94a3b8; font-size:0.85rem;">Source: ${escapeHtml(sourceTag)}</div>
  `);
}

async function processPayload(payload, sourceTag) {
  const parsed = parseQrPayload(payload);
  if (!parsed.ok) {
    setStatus('fake', 'INVALID QR');
    renderCardHtml(`<div class="fail">Credential Invalid ❌</div><div>${escapeHtml(parsed.reason)}</div>`);
    return;
  }

  if (await isQrAlreadyConsumed(parsed.qk)) {
    setStatus('fake', 'ALREADY USED');
    renderCardHtml('<div class="fail">Credential Invalid ❌</div><div>This QR has already been used once on this verifier device.</div>');
    return;
  }

  try {
    const decodedQd = await decodeQdPayload(parsed.qd);
    const decoded = decodedQd.parsed;
    const offlineCheck = await verifyJwsToken(parsed.qk, decodedQd.payloadText, parsed.credentialId);
    if (offlineCheck && offlineCheck.ok) {
      await markQrConsumed(parsed.qk, parsed.credentialId);
    }
    renderDecodedSecret(decoded, sourceTag, offlineCheck);
  } catch (e) {
    setStatus('fake', 'INVALID');
    renderCardHtml(`<div class="fail">Credential Invalid ❌</div><div>${escapeHtml(String(e))}</div>`);
  }
}

// Keep repeat scans valid on the same device; local storage is only a warning, not proof of fraud.
processPayload = async function processPayloadOverride(payload, sourceTag) {
  const parsed = parseQrPayload(payload);
  if (!parsed.ok) {
    setStatus('fake', 'INVALID QR');
    renderCardHtml(`<div class="fail">Credential Invalid âŒ</div><div>${escapeHtml(parsed.reason)}</div>`);
    return;
  }

  try {
    const alreadyConsumed = await isQrAlreadyConsumed(parsed.qk);
    const decodedQd = await decodeQdPayload(parsed.qd);
    const decoded = decodedQd.parsed;
    const offlineCheck = await verifyJwsToken(parsed.qk, decodedQd.payloadText, parsed.credentialId);

    if (offlineCheck && offlineCheck.ok && !alreadyConsumed) {
      await markQrConsumed(parsed.qk, parsed.credentialId);
    }

    const offlineReason = String(offlineCheck?.reason || '');
    const repeatedScanReason = alreadyConsumed
      ? `${offlineReason}${offlineReason ? '. ' : ''}This QR was already scanned on this device earlier.`
      : offlineReason;

    renderDecodedSecret(decoded, sourceTag, {
      ...offlineCheck,
      reason: repeatedScanReason
    });
  } catch (e) {
    setStatus('fake', 'INVALID');
    renderCardHtml(`<div class="fail">Credential Invalid âŒ</div><div>${escapeHtml(String(e))}</div>`);
  }
}

function getLandingPayloadFromPageUrl() {
  const params = new URLSearchParams(window.location.search);
  if (!params.get('id') || !params.get('qk') || !params.get('qd')) {
    return null;
  }
  return window.location.href;
}

async function startCameraScan() {
  if (activeVideoTrack) return;

  startScanBtn.disabled = true;
  stopScanBtn.disabled = false;

  await codeReader.decodeFromVideoDevice(null, camera, (result) => {
    if (result && result.text) {
      stopCameraScan();
      processPayload(result.text, 'camera');
    }
  });

  const mediaStream = camera.srcObject;
  if (mediaStream && mediaStream.getVideoTracks) {
    activeVideoTrack = mediaStream.getVideoTracks()[0] || null;
  }
}

function stopCameraScan() {
  try {
    codeReader.reset();
  } catch {
    // no-op
  }

  if (activeVideoTrack) {
    try {
      activeVideoTrack.stop();
    } catch {
      // no-op
    }
    activeVideoTrack = null;
  }

  camera.srcObject = null;
  startScanBtn.disabled = false;
  stopScanBtn.disabled = true;
}

startScanBtn.addEventListener('click', () => {
  startCameraScan().catch(err => {
    setStatus('suspicious', 'CAMERA ERROR');
    renderCardHtml(`<div class="fail">Camera error ❌</div><div>${escapeHtml(String(err))}</div>`);
  });
});

stopScanBtn.addEventListener('click', stopCameraScan);

verifyLinkBtn.addEventListener('click', () => {
  const link = (qrLinkInput.value || '').trim();
  if (!link) {
    setStatus('fake', 'INVALID LINK');
    renderCardHtml('<div class="fail">Credential Invalid ❌</div><div>Please paste a QR verification link.</div>');
    return;
  }
  processPayload(link, 'link-paste');
});

qrFile.addEventListener('change', async (e) => {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  let imageUrl = null;

  try {
    imageUrl = URL.createObjectURL(file);
    const imgEl = new Image();
    imgEl.src = imageUrl;
    await new Promise((resolve, reject) => {
      imgEl.onload = resolve;
      imgEl.onerror = reject;
    });

    const result = await codeReader.decodeFromImageElement(imgEl);
    if (!result || !result.text) {
      setStatus('fake', 'INVALID QR');
      renderCardHtml('<div class="fail">Credential Invalid ❌</div><div>No readable QR found in uploaded image.</div>');
      return;
    }

    processPayload(result.text, 'upload');
  } catch {
    setStatus('fake', 'INVALID QR');
    renderCardHtml('<div class="fail">Credential Invalid ❌</div><div>No readable QR found in uploaded image.</div>');
  } finally {
    if (imageUrl) {
      URL.revokeObjectURL(imageUrl);
    }
  }
});

(function init() {
  renderCardHtml('Waiting for scan...');
  loadIssuerRegistry().then(ok => {
    if (!ok) {
      setStatus('fake', 'INVALID');
      renderCardHtml('<div class="fail">Verifier not configured ❌</div><div>trusted_issuers.json is missing, so signature validation cannot run.</div>');
    }
  });
})();

(async function autoVerifyLandingUrl() {
  const landingPayload = getLandingPayloadFromPageUrl();
  if (!landingPayload) {
    return;
  }

  const ok = await loadIssuerRegistry();
  if (!ok) {
    return;
  }

  qrLinkInput.value = landingPayload;
  setStatus('pending', 'VERIFYING');
  renderCardHtml('<div>QR payload detected in page URL. Verifying now...</div>');
  processPayload(landingPayload, 'landing-url');
})();
