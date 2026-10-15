import { ApiError, downloadUrl, query, request } from "@/lib/api";

describe("api helpers", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("builds query strings without empty values", () => {
    expect(query({ a: "x", b: undefined, c: null, d: "", e: 0, f: false })).toBe("?a=x&e=0&f=false");
    expect(query({})).toBe("");
    expect(downloadUrl("/events", { format: "csv" })).toBe("/api/v1/events?format=csv");
  });

  it("sends JSON and parses the response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(request("POST", "/evaluate", { action: "x" })).resolves.toEqual({ ok: true });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/evaluate");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ action: "x" }));
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
  });

  it("raises ApiError with the server's detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: [{ msg: "bad severity" }] }), { status: 422 })));
    const error = await request("GET", "/x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(422);
    expect((error as ApiError).message).toBe("bad severity");
  });
});
