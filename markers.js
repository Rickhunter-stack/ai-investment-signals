let AIS_MARKERS=[];
fetch('/data/markers.json').then(r=>r.ok?r.json():[]).then(data=>{AIS_MARKERS=Array.isArray(data)?data:[]; if(window.priceChart) window.priceChart.update();}).catch(()=>{});

const aisMarkerPlugin={
  id:'aisMarkers',
  afterDatasetsDraw(chart){
    if(chart.canvas.id!=='priceChart' || typeof selected==='undefined') return;
    const labels=(chart.data.labels||[]).map(String);
    if(!labels.length) return;
    const x=chart.scales.x, y=chart.scales.y, ctx=chart.ctx;
    const marks=AIS_MARKERS.filter(m=>m.ticker===selected && m.date);
    marks.forEach((m,j)=>{
      let best=-1,dist=Infinity;
      labels.forEach((d,i)=>{const delta=Math.abs(new Date(d)-new Date(m.date)); if(delta<dist){dist=delta;best=i;}});
      if(best<0) return;
      const px=x.getPixelForValue(best), top=y.top+11+(j%3)*3;
      ctx.save();
      ctx.strokeStyle=m.kind==='brief'?'rgba(95,196,203,.55)':'rgba(219,176,90,.55)';
      ctx.lineWidth=1; ctx.setLineDash([4,4]);
      ctx.beginPath(); ctx.moveTo(px,top+8); ctx.lineTo(px,y.bottom); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle=m.kind==='brief'?'#5fc4cb':'#dbb05a';
      ctx.beginPath(); ctx.arc(px,top,7,0,Math.PI*2); ctx.fill();
      ctx.fillStyle='#0d1214'; ctx.font='bold 9px system-ui'; ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(m.kind==='brief'?'B':'E',px,top+.5);
      ctx.restore();
    });
  }
};
Chart.register(aisMarkerPlugin);
