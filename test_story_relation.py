import importlib.util
from pathlib import Path

P = Path(__file__).parent / "scripts" / "classify_story_relation.py"
spec = importlib.util.spec_from_file_location("story", P)
story = importlib.util.module_from_spec(spec); spec.loader.exec_module(story)

BASE = {"event_id":"EVT-A","frozen":True,"title":"HBM capacity sold out","factual_summary":"HBM memory demand exceeds supply","theme":"IA et semi-conducteurs","subtheme":"HBM / memory","sector":"Semiconductors","tickers":["MU"],"companies":["Micron"],"direction":"positive","importance":70,"story":{"story_id":"STORY-HBM","relation":"NEW"}}

def new(**kw):
    x = dict(BASE); x.update({"event_id":"EVT-B","frozen":True}); x.update(kw); return x

def test_new_unrelated():
    x = new(title="Medical robot approval", factual_summary="FDA clears a surgical robot", theme="Santé", subtheme="robotique médicale", sector="Medical devices", tickers=["ISRG"], companies=["Intuitive Surgical"])
    assert story.classify(x,[BASE])["relation"] == "NEW"

def test_confirm_same_story():
    r = story.classify(new(title="HBM demand remains above supply", factual_summary="Micron confirms strong HBM memory demand"), [BASE])
    assert r["story_id"] == "STORY-HBM" and r["relation"] in {"CONFIRM","REPEAT"}

def test_accelerate():
    r = story.classify(new(importance=92, title="HBM shortage intensifies", factual_summary="HBM memory demand exceeds supply further"), [BASE])
    assert r["relation"] == "ACCELERATE"

def test_contradict():
    r = story.classify(new(direction="negative", title="HBM oversupply emerges", factual_summary="Micron HBM memory supply now exceeds demand"), [BASE])
    assert r["relation"] == "CONTRADICT"
