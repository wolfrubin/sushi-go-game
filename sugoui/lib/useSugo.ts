import { useEffect, useState, useSyncExternalStore } from 'react';
import { defaultSocketUrl, SugoClient } from './client';
import type { Snapshot } from './client';

const SERVER_SNAPSHOT: Snapshot = { status: 'closed', state: null, sessionLost: false };

/** One shared connection to the game server for the page. */
export function useSugo() {
  const [client] = useState(() => new SugoClient({ url: '' }));

  useEffect(() => {
    // Built here, not at render, because it needs window.location
    client.setUrl(defaultSocketUrl(window.location));
    client.connect();
    return () => client.close();
  }, [client]);

  const snapshot = useSyncExternalStore(client.subscribe, client.getSnapshot, () => SERVER_SNAPSHOT);
  return { client, ...snapshot };
}
