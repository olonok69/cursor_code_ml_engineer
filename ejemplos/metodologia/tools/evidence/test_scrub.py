from evidence.scrub import scrub

SIGNED = ("Data to process: {'file_url': 'https://b.s3.<region>.amazonaws.com/uploads/1/A.docx"
          "?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAQ3EXAMPLEKEY1234%2F20261015%2Fxx-region-1"
          "&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEXAMPLE&X-Amz-Signature=abc123', 'doc_id': 1}")

def test_scrub_removes_presigned_query():
    out = scrub(SIGNED)
    assert "X-Amz-Credential" not in out and "X-Amz-Signature" not in out and "Security-Token" not in out
    assert "?<presigned-signature-removed>" in out
    assert "uploads/1/A.docx" in out          # the key survives
    assert "'doc_id': 1" in out                    # the rest of the line survives

def test_scrub_removes_bare_access_key():
    assert "ASIAQ3EXAMPLEKEY1234" not in scrub("key=ASIAQ3EXAMPLEKEY1234 end")

def test_scrub_leaves_clean_text():
    assert scrub("Started processing document 1001") == "Started processing document 1001"
