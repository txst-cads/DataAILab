const timestamp = Date.now();
const testDataUrl = '/data/visualization-data.json?v=' + timestamp;
console.log('Testing URL:', testDataUrl);
fetch(testDataUrl)
  .then(response => response.json())
  .then(data => {
    console.log('✅ Test fetch successful');
    console.log('Keys:', Object.keys(data));
    console.log('Publications:', data.p ? data.p.length : 'missing');
    console.log('Researchers:', data.r ? data.r.length : 'missing');
    console.log('Clusters:', data.c ? data.c.length : 'missing');
  })
  .catch(err => console.error('❌ Test fetch failed:', err));
