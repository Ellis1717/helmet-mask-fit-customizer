// Photo calibration runs entirely in the browser; photo pixels never leave the page.
// Each view takes 4 clicks: reference start/end, then head span start/end.
(() => {
  const views = {};
  const $ = id => document.getElementById(id);
  for (const side of ['front', 'side']) {
    const canvas = $('photo_' + side), ctx = canvas.getContext('2d');
    const state = { image: null, points: [] }; views[side] = state;
    const message = () => {
      const prompts = ['Click reference point 1', 'Click reference point 2',
        'Click head span point 1', 'Click head span point 2', 'Four points set — calculate or reset'];
      $('status_' + side).textContent = prompts[state.points.length];
    };
    function redraw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (state.image) ctx.drawImage(state.image, 0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 2;
      state.points.forEach((p, i) => {
        ctx.fillStyle = i < 2 ? '#ffd166' : '#67e8f9';
        ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, Math.PI * 2); ctx.fill();
      });
      for (const [a, b, color] of [[0,1,'#ffd166'],[2,3,'#67e8f9']]) {
        if (state.points[b]) {
          ctx.strokeStyle = color; ctx.beginPath();
          ctx.moveTo(state.points[a].x, state.points[a].y);
          ctx.lineTo(state.points[b].x, state.points[b].y); ctx.stroke();
        }
      }
    }
    $('upload_' + side).addEventListener('change', event => {
      const file = event.target.files[0]; if (!file) return;
      if (!file.type.startsWith('image/')) { alert('Select an image.'); return; }
      const url = URL.createObjectURL(file), image = new Image();
      image.onload = () => {
        const ratio = image.width / image.height;
        canvas.width = Math.min(700, Math.round(450 * ratio));
        canvas.height = Math.round(canvas.width / ratio);
        state.image = image; state.points = []; redraw(); message(); URL.revokeObjectURL(url);
      };
      image.onerror = () => { URL.revokeObjectURL(url); alert('Unable to read photo.'); };
      image.src = url;
    });
    canvas.addEventListener('click', event => {
      if (!state.image || state.points.length === 4) return;
      const r = canvas.getBoundingClientRect();
      state.points.push({ x: (event.clientX-r.left)*canvas.width/r.width,
        y: (event.clientY-r.top)*canvas.height/r.height });
      redraw(); message();
    });
    $('reset_' + side).addEventListener('click', () => { state.points=[]; redraw(); message(); });
    message();
  }
  const dist = (a,b) => Math.hypot(a.x-b.x,a.y-b.y);
  $('apply_calibration').addEventListener('click', () => {
    try {
      const updates = {};
      for (const [side, field] of [['front','head_width'], ['side','head_depth']]) {
        const s = views[side]; if (s.points.length !== 4) throw Error('Add all four points in each photo.');
        const ref = Number($('reference_' + side).value);
        if (!Number.isFinite(ref) || ref <= 0) throw Error('Reference length must be positive.');
        const refPixels = dist(s.points[0], s.points[1]);
        const spanPixels = dist(s.points[2], s.points[3]);
        if (refPixels < 10 || spanPixels < 10) throw Error('Reference or head span is too short in '+side+' image.');
        const mm = ref * spanPixels / refPixels;
        if (mm < 30 || mm > 500) throw Error('Unreasonable measurement: '+mm.toFixed(1)+'mm. Recheck points.');
        updates[field] = mm;
      }
      for (const [field,mm] of Object.entries(updates)) $(field).value = mm.toFixed(1);
      $('calibration_result').textContent = 'Updated head width '+updates.head_width.toFixed(1)+'mm and depth '+updates.head_depth.toFixed(1)+'mm. Measure height separately.';
    } catch (error) { $('calibration_result').textContent = error.message; }
  });
  const profileIds = ['head_width','head_depth','head_height','clearance','pad_front','pad_back','pad_left','pad_right','pad_crown'];
  $('export_profile').addEventListener('click', () => {
    const values = Object.fromEntries(profileIds.map(id => [id,Number($(id).value)]));
    const profile = { schema_version:1, units:'mm', values,
      method:'manual and/or photo reference calibration',
      caution:'Photos are not included. Verify dimensions before printing.' };
    const blob = new Blob([JSON.stringify(profile,null,2)],{type:'application/json'});
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href=url; a.download='head_fit_profile.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  });
  $('import_profile').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    try {
      if (file.size > 100000) throw Error('Profile JSON too large.');
      const profile = JSON.parse(await file.text());
      if (profile.schema_version !== 1 || profile.units !== 'mm') throw Error('Unsupported profile format.');
      for (const id of profileIds) {
        const value = profile.values?.[id];
        const lower = id.startsWith('head_') ? 30 : 0;
        const upper = id.startsWith('head_') ? 500 : id === 'clearance' ? 30 : 35;
        if (typeof value !== 'number' || !Number.isFinite(value) || value < lower || value > upper)
          throw Error('Invalid profile field: ' + id);
      }
      for (const id of profileIds) $(id).value = profile.values[id];
      $('calibration_result').textContent = 'Profile imported successfully (measurements and padding only).';
    } catch (err) { $('calibration_result').textContent = err.message; }
    event.target.value='';
  });
})();