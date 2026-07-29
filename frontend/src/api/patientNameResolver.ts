const resolverUrl = import.meta.env.VITE_PATIENT_NAME_RESOLVER_URL as string | undefined;

type ResolverResponse = {
  name?: string;
  nm_paciente?: string;
};

export async function resolvePatientName(cdPaciente: string, cdAtendimento?: string): Promise<string | null> {
  if (!resolverUrl) return null;

  const baseUrl = resolverUrl.replace(/\/$/, '');
  const url = new URL(`${baseUrl}/patients/${encodeURIComponent(cdPaciente)}`);
  if (cdAtendimento) {
    url.searchParams.set('cd_atendimento', cdAtendimento);
  }

  try {
    const response = await fetch(url.toString(), { method: 'GET', mode: 'cors' });
    if (!response.ok) return null;
    const data = (await response.json()) as ResolverResponse;
    return data.name || data.nm_paciente || null;
  } catch {
    return null;
  }
}
