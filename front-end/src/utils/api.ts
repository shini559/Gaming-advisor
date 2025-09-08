async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    // Si pas de refresh token, on ne peut rien faire, l'utilisateur doit se reconnecter
    console.error('No refresh token found');
    // On redirige vers la page de login
    window.location.href = '/login';
    return null;
  }

  try {
    const response = await fetch('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    // On met à jour les tokens dans le localStorage
    localStorage.setItem('access_token', data.access_token);
    // L'API peut aussi renvoyer un nouveau refresh token
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }

    return data.access_token;

  } catch (error) {
    console.error('Could not refresh token:', error);
    // Si le refresh échoue, l'utilisateur doit se reconnecter
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
    return null;
  }
}


export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let accessToken = localStorage.getItem('access_token');
  let refreshed = false;

  // On ajoute le token d'accès à la requête
  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  };

  // On fait le premier appel
  let response = await fetch(url, options);

  // Si l'appel échoue avec une erreur 401 (token expiré)
  if (response.status === 401) {
    console.log('Access token expired. Refreshing...');
    // On essaie de rafraîchir le token
    const newAccessToken = await refreshToken();

    if (newAccessToken) {
      refreshed = true;
      // Si on a un nouveau token, on met à jour les headers et on réessaie la requête
      options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${newAccessToken}`,
      };
      console.log('Retrying the request with new token...');
      response = await fetch(url, options);
    }
  }

  return { response, refreshed };
}
export async function uploadFileWithAuth(url: string, files: FileList) {
  const formData = new FormData();

  // On boucle sur les fichiers et on les ajoute tous avec la même clé "files"
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  let accessToken = localStorage.getItem('access_token');
  const headers = {
    'Authorization': `Bearer ${accessToken}`,
  };

  let response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (response.status === 401) {
    console.log('Access token expired. Refreshing...');
    const newAccessToken = await refreshToken();

    if (newAccessToken) {
      headers['Authorization'] = `Bearer ${newAccessToken}`;
      console.log('Retrying the upload with new token...');
      response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });
    }
  }

  return response;
}