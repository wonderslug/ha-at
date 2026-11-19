// node_modules/@lit/reactive-element/css-tag.js
var e = globalThis, t = e.ShadowRoot && (e.ShadyCSS === void 0 || e.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, n = Symbol(), r = /* @__PURE__ */ new WeakMap(), i = class {
	constructor(e, t, r) {
		if (this._$cssResult$ = !0, r !== n) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
		this.cssText = e, this.t = t;
	}
	get styleSheet() {
		let e = this.o, n = this.t;
		if (t && e === void 0) {
			let t = n !== void 0 && n.length === 1;
			t && (e = r.get(n)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), t && r.set(n, e));
		}
		return e;
	}
	toString() {
		return this.cssText;
	}
}, a = (e) => new i(typeof e == "string" ? e : e + "", void 0, n), o = (e, ...t) => new i(e.length === 1 ? e[0] : t.reduce((t, n, r) => t + ((e) => {
	if (!0 === e._$cssResult$) return e.cssText;
	if (typeof e == "number") return e;
	throw Error("Value passed to 'css' function must be a 'css' function result: " + e + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
})(n) + e[r + 1], e[0]), e, n), s = (n, r) => {
	if (t) n.adoptedStyleSheets = r.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
	else for (let t of r) {
		let r = document.createElement("style"), i = e.litNonce;
		i !== void 0 && r.setAttribute("nonce", i), r.textContent = t.cssText, n.appendChild(r);
	}
}, c = t ? (e) => e : (e) => e instanceof CSSStyleSheet ? ((e) => {
	let t = "";
	for (let n of e.cssRules) t += n.cssText;
	return a(t);
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: ee, getOwnPropertySymbols: te, getPrototypeOf: ne } = Object, f = globalThis, re = f.trustedTypes, ie = re ? re.emptyScript : "", ae = f.reactiveElementPolyfillSupport, p = (e, t) => e, m = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? ie : null;
				break;
			case Object:
			case Array: e = e == null ? e : JSON.stringify(e);
		}
		return e;
	},
	fromAttribute(e, t) {
		let n = e;
		switch (t) {
			case Boolean:
				n = e !== null;
				break;
			case Number:
				n = e === null ? null : Number(e);
				break;
			case Object:
			case Array: try {
				n = JSON.parse(e);
			} catch {
				n = null;
			}
		}
		return n;
	}
}, h = (e, t) => !l(e, t), oe = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	useDefault: !1,
	hasChanged: h
};
Symbol.metadata ??= Symbol("metadata"), f.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var g = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = oe) {
		if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
			let n = Symbol(), r = this.getPropertyDescriptor(e, n, t);
			r !== void 0 && u(this.prototype, e, r);
		}
	}
	static getPropertyDescriptor(e, t, n) {
		let { get: r, set: i } = d(this.prototype, e) ?? {
			get() {
				return this[t];
			},
			set(e) {
				this[t] = e;
			}
		};
		return {
			get: r,
			set(t) {
				let a = r?.call(this);
				i?.call(this, t), this.requestUpdate(e, a, n);
			},
			configurable: !0,
			enumerable: !0
		};
	}
	static getPropertyOptions(e) {
		return this.elementProperties.get(e) ?? oe;
	}
	static _$Ei() {
		if (this.hasOwnProperty(p("elementProperties"))) return;
		let e = ne(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(p("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(p("properties"))) {
			let e = this.properties, t = [...ee(e), ...te(e)];
			for (let n of t) this.createProperty(n, e[n]);
		}
		let e = this[Symbol.metadata];
		if (e !== null) {
			let t = litPropertyMetadata.get(e);
			if (t !== void 0) for (let [e, n] of t) this.elementProperties.set(e, n);
		}
		this._$Eh = /* @__PURE__ */ new Map();
		for (let [e, t] of this.elementProperties) {
			let n = this._$Eu(e, t);
			n !== void 0 && this._$Eh.set(n, e);
		}
		this.elementStyles = this.finalizeStyles(this.styles);
	}
	static finalizeStyles(e) {
		let t = [];
		if (Array.isArray(e)) {
			let n = new Set(e.flat(1 / 0).reverse());
			for (let e of n) t.unshift(c(e));
		} else e !== void 0 && t.push(c(e));
		return t;
	}
	static _$Eu(e, t) {
		let n = t.attribute;
		return !1 === n ? void 0 : typeof n == "string" ? n : typeof e == "string" ? e.toLowerCase() : void 0;
	}
	constructor() {
		super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
	}
	_$Ev() {
		this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((e) => e(this));
	}
	addController(e) {
		(this._$EO ??= /* @__PURE__ */ new Set()).add(e), this.renderRoot !== void 0 && this.isConnected && e.hostConnected?.();
	}
	removeController(e) {
		this._$EO?.delete(e);
	}
	_$E_() {
		let e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
		for (let n of t.keys()) this.hasOwnProperty(n) && (e.set(n, this[n]), delete this[n]);
		e.size > 0 && (this._$Ep = e);
	}
	createRenderRoot() {
		let e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
		return s(e, this.constructor.elementStyles), e;
	}
	connectedCallback() {
		this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
	}
	enableUpdating(e) {}
	disconnectedCallback() {
		this._$EO?.forEach((e) => e.hostDisconnected?.());
	}
	attributeChangedCallback(e, t, n) {
		this._$AK(e, n);
	}
	_$ET(e, t) {
		let n = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, n);
		if (r !== void 0 && !0 === n.reflect) {
			let i = (n.converter?.toAttribute === void 0 ? m : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? m : e.converter;
			this._$Em = r;
			let a = i.fromAttribute(t, e.type);
			this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
		}
	}
	requestUpdate(e, t, n, r = !1, i) {
		if (e !== void 0) {
			let a = this.constructor;
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? h)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
			this.C(e, t, n);
		}
		!1 === this.isUpdatePending && (this._$ES = this._$EP());
	}
	C(e, t, { useDefault: n, reflect: r, wrapped: i }, a) {
		n && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, a ?? t ?? this[e]), !0 !== i || a !== void 0) || (this._$AL.has(e) || (this.hasUpdated || n || (t = void 0), this._$AL.set(e, t)), !0 === r && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
	}
	async _$EP() {
		this.isUpdatePending = !0;
		try {
			await this._$ES;
		} catch (e) {
			Promise.reject(e);
		}
		let e = this.scheduleUpdate();
		return e != null && await e, !this.isUpdatePending;
	}
	scheduleUpdate() {
		return this.performUpdate();
	}
	performUpdate() {
		if (!this.isUpdatePending) return;
		if (!this.hasUpdated) {
			if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
				for (let [e, t] of this._$Ep) this[e] = t;
				this._$Ep = void 0;
			}
			let e = this.constructor.elementProperties;
			if (e.size > 0) for (let [t, n] of e) {
				let { wrapped: e } = n, r = this[t];
				!0 !== e || this._$AL.has(t) || r === void 0 || this.C(t, void 0, n, r);
			}
		}
		let e = !1, t = this._$AL;
		try {
			e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((e) => e.hostUpdate?.()), this.update(t)) : this._$EM();
		} catch (t) {
			throw e = !1, this._$EM(), t;
		}
		e && this._$AE(t);
	}
	willUpdate(e) {}
	_$AE(e) {
		this._$EO?.forEach((e) => e.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
	}
	_$EM() {
		this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
	}
	get updateComplete() {
		return this.getUpdateComplete();
	}
	getUpdateComplete() {
		return this._$ES;
	}
	shouldUpdate(e) {
		return !0;
	}
	update(e) {
		this._$Eq &&= this._$Eq.forEach((e) => this._$ET(e, this[e])), this._$EM();
	}
	updated(e) {}
	firstUpdated(e) {}
};
g.elementStyles = [], g.shadowRootOptions = { mode: "open" }, g[p("elementProperties")] = /* @__PURE__ */ new Map(), g[p("finalized")] = /* @__PURE__ */ new Map(), ae?.({ ReactiveElement: g }), (f.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var _ = globalThis, se = (e) => e, v = _.trustedTypes, ce = v ? v.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, le = "$lit$", y = `lit$${Math.random().toFixed(9).slice(2)}$`, ue = "?" + y, de = `<${ue}>`, b = document, x = () => b.createComment(""), S = (e) => e === null || typeof e != "object" && typeof e != "function", C = Array.isArray, fe = (e) => C(e) || typeof e?.[Symbol.iterator] == "function", w = "[ 	\n\f\r]", T = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, E = /-->/g, pe = />/g, D = RegExp(`>|${w}(?:([^\\s"'>=/]+)(${w}*=${w}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), me = /'/g, O = /"/g, he = /^(?:script|style|textarea|title)$/i, k = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), A = Symbol.for("lit-noChange"), j = Symbol.for("lit-nothing"), ge = /* @__PURE__ */ new WeakMap(), M = b.createTreeWalker(b, 129);
function _e(e, t) {
	if (!C(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return ce === void 0 ? t : ce.createHTML(t);
}
var ve = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = T;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === T ? c[1] === "!--" ? o = E : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = D) : (he.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = D) : o = pe : o === D ? c[0] === ">" ? (o = i ?? T, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? D : c[3] === "\"" ? O : me) : o === O || o === me ? o = D : o === E || o === pe ? o = T : (o = D, i = void 0);
		let d = o === D && e[t + 1].startsWith("/>") ? " " : "";
		a += o === T ? n + de : l >= 0 ? (r.push(s), n.slice(0, l) + le + n.slice(l) + y + d) : n + y + (l === -2 ? t : d);
	}
	return [_e(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, N = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = ve(t, n);
		if (this.el = e.createElement(l, r), M.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = M.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(le)) {
					let t = u[o++], n = i.getAttribute(e).split(y), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? be : r[1] === "?" ? xe : r[1] === "@" ? Se : I
					}), i.removeAttribute(e);
				} else e.startsWith(y) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (he.test(i.tagName)) {
					let e = i.textContent.split(y), t = e.length - 1;
					if (t > 0) {
						i.textContent = v ? v.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], x()), M.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], x());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === ue) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(y, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += y.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = b.createElement("template");
		return n.innerHTML = e, n;
	}
};
function P(e, t, n = e, r) {
	if (t === A) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = S(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = P(e, i._$AS(e, t.values), i, r)), t;
}
var ye = class {
	constructor(e, t) {
		this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
	}
	get parentNode() {
		return this._$AM.parentNode;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	u(e) {
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? b).importNode(t, !0);
		M.currentNode = r;
		let i = M.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new F(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Ce(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = M.nextNode(), a++);
		}
		return M.currentNode = b, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, F = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = j, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
	}
	get parentNode() {
		let e = this._$AA.parentNode, t = this._$AM;
		return t !== void 0 && e?.nodeType === 11 && (e = t.parentNode), e;
	}
	get startNode() {
		return this._$AA;
	}
	get endNode() {
		return this._$AB;
	}
	_$AI(e, t = this) {
		e = P(this, e, t), S(e) ? e === j || e == null || e === "" ? (this._$AH !== j && this._$AR(), this._$AH = j) : e !== this._$AH && e !== A && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? fe(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== j && S(this._$AH) ? this._$AA.nextSibling.data = e : this.T(b.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = N.createElement(_e(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new ye(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = ge.get(e.strings);
		return t === void 0 && ge.set(e.strings, t = new N(e)), t;
	}
	k(t) {
		C(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(x()), this.O(x()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = se(e).nextSibling;
			se(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, I = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = j, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = j;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = P(this, e, t, 0), a = !S(e) || e !== this._$AH && e !== A, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = P(this, r[n + o], t, o), s === A && (s = this._$AH[o]), a ||= !S(s) || s !== this._$AH[o], s === j ? e = j : e !== j && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === j ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, be = class extends I {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === j ? void 0 : e;
	}
}, xe = class extends I {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== j);
	}
}, Se = class extends I {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = P(this, e, t, 0) ?? j) === A) return;
		let n = this._$AH, r = e === j && n !== j || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== j && (n === j || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Ce = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		P(this, e);
	}
}, we = _.litHtmlPolyfillSupport;
we?.(N, F), (_.litHtmlVersions ??= []).push("3.3.3");
var Te = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new F(t.insertBefore(x(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, L = globalThis, R = class extends g {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Te(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return A;
	}
};
R._$litElement$ = !0, R.finalized = !0, L.litElementHydrateSupport?.({ LitElement: R });
var Ee = L.litElementPolyfillSupport;
Ee?.({ LitElement: R }), (L.litElementVersions ??= []).push("4.2.2");
// node_modules/@lit/reactive-element/decorators/custom-element.js
var z = (e) => (t, n) => {
	n === void 0 ? customElements.define(e, t) : n.addInitializer(() => {
		customElements.define(e, t);
	});
}, De = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	hasChanged: h
}, Oe = (e = De, t, n) => {
	let { kind: r, metadata: i } = n, a = globalThis.litPropertyMetadata.get(i);
	if (a === void 0 && globalThis.litPropertyMetadata.set(i, a = /* @__PURE__ */ new Map()), r === "setter" && ((e = Object.create(e)).wrapped = !0), a.set(n.name, e), r === "accessor") {
		let { name: r } = n;
		return {
			set(n) {
				let i = t.get.call(this);
				t.set.call(this, n), this.requestUpdate(r, i, e, !0, n);
			},
			init(t) {
				return t !== void 0 && this.C(r, void 0, e, t), t;
			}
		};
	}
	if (r === "setter") {
		let { name: r } = n;
		return function(n) {
			let i = this[r];
			t.call(this, n), this.requestUpdate(r, i, e, !0, n);
		};
	}
	throw Error("Unsupported decorator location: " + r);
};
function B(e) {
	return (t, n) => typeof n == "object" ? Oe(e, t, n) : ((e, t, n) => {
		let r = t.hasOwnProperty(n);
		return t.constructor.createProperty(n, e), r ? Object.getOwnPropertyDescriptor(t, n) : void 0;
	})(e, t, n);
}
// node_modules/@lit/reactive-element/decorators/state.js
function V(e) {
	return B({
		...e,
		state: !0,
		attribute: !1
	});
}
// src/api.ts
function ke(e, t) {
	return e.connection.subscribeMessage(t, { type: "at/subscribe" });
}
function Ae(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/parse",
		text: t
	});
}
function je(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/schedule",
		...t
	});
}
function Me(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/cancel",
		job_ids: t
	});
}
function Ne(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/run_now",
		job_id: t
	});
}
function Pe(e, t, n) {
	return e.connection.sendMessagePromise({
		type: "at/reschedule",
		job_id: t,
		due: n
	});
}
function Fe(e) {
	return e.connection.sendMessagePromise({ type: "at/clear_history" });
}
function Ie(e) {
	return e.connection.sendMessagePromise({ type: "at/info" });
}
// src/add-job.ts
function H(e) {
	if ("verb" in e) return [{
		action: `homeassistant.${e.verb}`,
		target: { entity_id: [...e.targetEntityIds] }
	}];
	if ("script" in e) {
		let t = {
			action: "script.turn_on",
			target: { entity_id: e.script }
		};
		return e.variables && Object.keys(e.variables).length > 0 && (t.data = { variables: e.variables }), [t];
	}
	return [{
		action: "automation.trigger",
		target: { entity_id: e.automation }
	}];
}
function Le(e, t) {
	return { delay_seconds: e === "+15m" ? 900 : 3600 };
}
function Re(e) {
	if (!e.trim()) return {
		ok: !0,
		value: {}
	};
	try {
		let t = JSON.parse(e);
		return t && typeof t == "object" && !Array.isArray(t) ? {
			ok: !0,
			value: t
		} : {
			ok: !1,
			error: "Must be a JSON object, like {\"key\": \"value\"}"
		};
	} catch {
		return {
			ok: !1,
			error: "Invalid JSON"
		};
	}
}
function U(e) {
	try {
		let t = JSON.parse(e);
		return Array.isArray(t) && t.length > 0 && t.every((e) => e && typeof e == "object" && !Array.isArray(e)) ? {
			ok: !0,
			value: t
		} : {
			ok: !1,
			error: "Must be a non-empty JSON list of action objects"
		};
	} catch {
		return {
			ok: !1,
			error: "Invalid JSON"
		};
	}
}
function ze(e, t) {
	return !Number.isNaN(e.getTime()) && e.getTime() > t.getTime();
}
// src/format.ts
var Be = 36e5, Ve = 864e5;
function He(e, t) {
	let n = e - t;
	if (n < 0 || n >= Be) return "";
	let r = Math.floor(n / 1e3), i = Math.floor(r / 60), a = r % 60;
	return `${String(i).padStart(2, "0")}:${String(a).padStart(2, "0")}`;
}
function Ue(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		timeZone: n,
		year: "numeric",
		month: "numeric",
		day: "numeric"
	}).format(e);
}
function W(e, t, n, r) {
	let i = new Intl.DateTimeFormat(n, {
		timeZone: r,
		hour: "numeric",
		minute: "2-digit"
	}).format(e);
	if (Ue(e, n, r) === Ue(t, n, r)) return i;
	let a = e.getTime() - t.getTime();
	return a > 0 && a < 7 * Ve ? `${new Intl.DateTimeFormat(n, {
		timeZone: r,
		weekday: "short"
	}).format(e)} ${i}` : `${new Intl.DateTimeFormat(n, {
		timeZone: r,
		month: "short",
		day: "numeric"
	}).format(e)}, ${i}`;
}
function G(e, t) {
	let n = new Intl.DateTimeFormat("en-US", {
		timeZone: t,
		hourCycle: "h23",
		year: "numeric",
		month: "numeric",
		day: "numeric",
		hour: "numeric",
		minute: "numeric",
		second: "numeric"
	}).formatToParts(new Date(e)), r = (e) => Number(n.find((t) => t.type === e)?.value);
	return Date.UTC(r("year"), r("month") - 1, r("day"), r("hour"), r("minute"), r("second")) - Math.floor(e / 1e3) * 1e3;
}
function We(e, t) {
	let n = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(e);
	if (!n) return /* @__PURE__ */ new Date(NaN);
	let r = Date.UTC(+n[1], n[2] - 1, +n[3], +n[4], +n[5]);
	for (let e = 0; e < 1440; e++) {
		let n = r + e * 6e4, i = [G(n - 864e5, t), G(n + 864e5, t)].map((e) => n - e).sort((e, t) => e - t);
		for (let e of i) if (e + G(e, t) === n) return new Date(e);
	}
	return new Date(r - G(r, t));
}
function Ge(e, t) {
	return new Date(e.getTime() + G(e.getTime(), t)).toISOString().slice(0, 16);
}
// \0@oxc-project+runtime@0.156.0/helpers/esm/decorate.js
function K(e, t, n, r) {
	var i = arguments.length, a = i < 3 ? t : r === null ? r = Object.getOwnPropertyDescriptor(t, n) : r, o;
	if (typeof Reflect == "object" && typeof Reflect.decorate == "function") a = Reflect.decorate(e, t, n, r);
	else for (var s = e.length - 1; s >= 0; s--) (o = e[s]) && (a = (i < 3 ? o(a) : i > 3 ? o(t, n, a) : o(t, n)) || a);
	return i > 3 && a && Object.defineProperty(t, n, a), a;
}
// src/components/add-job-dialog.ts
var Ke = [
	"light",
	"switch",
	"fan",
	"cover",
	"input_boolean",
	"climate",
	"media_player",
	"lock",
	"humidifier",
	"siren",
	"vacuum"
], q = class extends R {
	constructor(...e) {
		super(...e), this.isAdmin = !1, this.open = !1, this.mode = "type", this.text = "", this.op = "turn_on", this.entity = "", this.varsText = "", this.chip = "+15m", this.when = "", this.rawText = "", this.error = "", this.busy = !1, this.parseSeq = 0, this.onKey = (e) => {
			e.key === "Escape" && this.open && this.close();
		};
	}
	connectedCallback() {
		super.connectedCallback(), window.addEventListener("keydown", this.onKey);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), window.removeEventListener("keydown", this.onKey), window.clearTimeout(this.debounce);
	}
	updated(e) {
		e.has("open") && this.open && this.reset();
	}
	reset() {
		window.clearTimeout(this.debounce), this.parseSeq++, this.mode = "type", this.text = "", this.preview = void 0, this.op = "turn_on", this.entity = "", this.varsText = "", this.chip = "+15m", this.when = "", this.rawText = "", this.error = "", this.busy = !1;
	}
	close() {
		this.reset(), this.open = !1, this.dispatchEvent(new CustomEvent("close-add-job"));
	}
	onText(e) {
		this.text = e, this.preview = void 0, this.error = "", window.clearTimeout(this.debounce);
		let t = ++this.parseSeq;
		if (!e.trim() || !this.hass) return;
		let n = this.hass;
		this.debounce = window.setTimeout(() => {
			Ae(n, e).then((e) => {
				if (t === this.parseSeq) {
					if (e.ok) {
						let t = W(new Date(e.due), /* @__PURE__ */ new Date(), this.locale, n.config.time_zone);
						this.preview = {
							ok: !0,
							text: `${e.summary} · ${t} ✓`
						};
					} else this.preview = {
						ok: !1,
						message: e.message
					};
				}
			}, (e) => {
				t === this.parseSeq && (this.preview = {
					ok: !1,
					message: e?.message || "Could not parse"
				});
			});
		}, 300);
	}
	get locale() {
		return this.hass?.locale?.language ?? this.hass?.language ?? "en";
	}
	get domains() {
		return this.op === "script" ? ["script"] : this.op === "automation" ? ["automation"] : Ke;
	}
	get entities() {
		let e = this.hass?.states ?? {};
		return Object.entries(e).filter(([e]) => this.domains.includes(e.split(".")[0])).map(([e, t]) => ({
			id: e,
			name: t.attributes.friendly_name || e
		})).sort((e, t) => e.name.localeCompare(t.name));
	}
	get vars() {
		return this.op === "script" ? Re(this.varsText) : {
			ok: !0,
			value: {}
		};
	}
	get whenValid() {
		return this.chip !== "" || ze(this.dueDate(), /* @__PURE__ */ new Date());
	}
	dueDate() {
		return We(this.when, this.hass?.config.time_zone ?? "UTC");
	}
	get canSubmit() {
		return this.busy || !this.hass ? !1 : this.mode === "type" ? this.preview?.ok === !0 : this.mode === "raw" ? this.rawText.trim() !== "" && this.whenValid : this.entity !== "" && this.vars.ok && this.whenValid;
	}
	buildPayload() {
		if (this.mode === "type") return { text: this.text };
		let e = this.mode === "raw", t;
		if (e) {
			let e = U(this.rawText);
			if (!e.ok) return e.error;
			t = e.value;
		} else if (this.op === "script") {
			let e = Re(this.varsText);
			if (!e.ok) return e.error;
			t = H({
				script: this.entity,
				variables: e.value
			});
		} else t = this.op === "automation" ? H({ automation: this.entity }) : H({
			targetEntityIds: [this.entity],
			verb: this.op
		});
		return this.chip ? {
			action: t,
			...Le(this.chip, /* @__PURE__ */ new Date())
		} : {
			action: t,
			due: this.dueDate().toISOString()
		};
	}
	async submit() {
		let e = this.hass;
		if (!e || !this.canSubmit) return;
		let t = this.buildPayload();
		if (typeof t == "string") this.error = t;
		else {
			this.busy = !0, this.error = "";
			try {
				await je(e, t), this.close();
			} catch (e) {
				this.error = e?.message || "Could not add the job";
			} finally {
				this.busy = !1;
			}
		}
	}
	setMode(e) {
		this.mode = e, this.error = "";
	}
	onChip(e) {
		this.chip = e, this.when = "";
	}
	onWhen(e) {
		this.when = e, this.chip = e ? "" : "+15m";
	}
	whenSection() {
		let e = this.hass?.config.time_zone ?? "UTC", t = Ge(/* @__PURE__ */ new Date(), e);
		return k`<div class="field">
      <span class="label">When</span>
      <div class="row">
        ${["+15m", "+1h"].map((e) => k`<button class="chip ${this.chip === e ? "on" : ""}" @click=${() => this.onChip(e)}>${e}</button>`)}
        <input type="datetime-local" aria-label="Date and time" .value=${this.when} min=${t} @input=${(e) => this.onWhen(e.target.value)} />
      </div>
      ${this.chip === "" && !this.whenValid ? k`<div class="inline-error">${this.when ? "Time must be in the future" : "Choose a time"}</div>` : j}
    </div>`;
	}
	pickSection() {
		let e = this.op === "script", t = this.vars;
		return k`
      <div class="field">
        <label class="label" for="op">Action</label>
        <select id="op" .value=${this.op} @change=${(e) => {
			this.op = e.target.value, this.entity = "";
		}}>
          <option value="turn_on">Turn on</option>
          <option value="turn_off">Turn off</option>
          <option value="toggle">Toggle</option>
          <option value="script">Run script</option>
          <option value="automation">Trigger automation</option>
        </select>
      </div>
      <div class="field">
        <label class="label" for="entity">Target</label>
        <select id="entity" .value=${this.entity} @change=${(e) => this.entity = e.target.value}>
          <option value="">Choose…</option>
          ${this.entities.map((e) => k`<option value=${e.id} ?selected=${e.id === this.entity}>${e.name}</option>`)}
        </select>
      </div>
      ${e ? k`<div class="field">
            <label class="label" for="vars">Variables (JSON, optional)</label>
            <textarea id="vars" rows="3" placeholder='{"brightness": 80}' .value=${this.varsText} @input=${(e) => this.varsText = e.target.value}></textarea>
            ${t.ok ? j : k`<div class="inline-error">${t.error}</div>`}
          </div>` : j}
      ${this.whenSection()}
    `;
	}
	typeSection() {
		return k`<div class="field">
      <label class="label" for="text">What should happen, and when?</label>
      <input id="text" type="text" placeholder="turn on the porch light at 11pm" .value=${this.text} @input=${(e) => this.onText(e.target.value)} />
      ${this.preview ? k`<div class=${this.preview.ok ? "preview ok" : "preview bad"}>${this.preview.ok ? this.preview.text : this.preview.message}</div>` : j}
    </div>`;
	}
	rawSection() {
		let e = this.rawText.trim() ? U(this.rawText) : void 0;
		return k`<div class="field">
        <label class="label" for="raw">Action list (JSON)</label>
        <textarea id="raw" rows="6" placeholder='[{"action": "light.turn_on", "target": {"entity_id": "light.porch"}}]' .value=${this.rawText} @input=${(e) => this.rawText = e.target.value}></textarea>
        ${e && !e.ok ? k`<div class="inline-error">${e.error}</div>` : j}
      </div>
      ${this.whenSection()}`;
	}
	tabBtn(e, t) {
		return k`<button class="mode ${this.mode === e ? "active" : ""}" role="tab" aria-selected=${this.mode === e} @click=${() => this.setMode(e)}>${t}</button>`;
	}
	render() {
		if (!this.open) return j;
		let e = this.mode === "raw" && this.rawText.trim() !== "" && !U(this.rawText).ok;
		return k`
      <div class="backdrop" @click=${() => this.close()}></div>
      <div class="dialog" role="dialog" aria-modal="true" aria-label="Add job">
        <h2>Add job</h2>
        <div class="modes" role="tablist">
          ${this.tabBtn("type", "Type it")} ${this.tabBtn("pick", "Pick it")} ${this.isAdmin ? this.tabBtn("raw", "Raw") : j}
        </div>
        ${this.mode === "type" ? this.typeSection() : this.mode === "pick" ? this.pickSection() : this.rawSection()}
        ${this.error ? k`<div class="error" role="alert">${this.error}</div>` : j}
        <div class="actions">
          <button @click=${() => this.close()}>Cancel</button>
          <button class="primary" ?disabled=${!this.canSubmit || e} @click=${() => void this.submit()}>Add</button>
        </div>
      </div>
    `;
	}
	static {
		this.styles = o`
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      z-index: 10;
    }
    .dialog {
      position: fixed;
      z-index: 11;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: min(480px, calc(100vw - 32px));
      max-height: calc(100vh - 32px);
      overflow: auto;
      box-sizing: border-box;
      padding: 16px 20px;
      background: var(--card-background-color);
      color: var(--primary-text-color);
      border-radius: 8px;
    }
    h2 {
      margin: 0 0 8px;
      font-size: 20px;
      font-weight: 400;
    }
    button {
      font: inherit;
      color: var(--primary-text-color);
      background: none;
      border: none;
      cursor: pointer;
      padding: 8px 12px;
    }
    .modes {
      display: flex;
      gap: 4px;
      margin-bottom: 8px;
    }
    .mode.active {
      color: var(--primary-color);
      border-bottom: 2px solid var(--primary-color);
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin: 12px 0;
    }
    .label {
      font-size: 13px;
      color: var(--secondary-text-color);
    }
    input,
    select,
    textarea {
      font: inherit;
      padding: 8px;
      color: var(--primary-text-color);
      background: var(--secondary-background-color, transparent);
      border: 1px solid var(--divider-color);
      border-radius: 4px;
    }
    textarea {
      font-family: monospace;
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .chip {
      border: 1px solid var(--divider-color);
      border-radius: 16px;
    }
    .chip.on {
      color: var(--text-primary-color, #fff);
      background: var(--primary-color);
    }
    .preview.ok {
      color: var(--success-color, #43a047);
    }
    .preview.bad,
    .inline-error {
      color: var(--error-color, #db4437);
      font-size: 13px;
    }
    .error {
      margin: 8px 0;
      padding: 8px 12px;
      border-radius: 4px;
      color: #fff;
      background: var(--error-color, #db4437);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
    .primary {
      color: var(--text-primary-color, #fff);
      background: var(--primary-color);
      border-radius: 4px;
    }
    .primary[disabled] {
      opacity: 0.5;
      cursor: default;
    }
  `;
	}
};
K([B({ attribute: !1 })], q.prototype, "hass", void 0), K([B({ type: Boolean })], q.prototype, "isAdmin", void 0), K([B({
	type: Boolean,
	reflect: !0
})], q.prototype, "open", void 0), K([V()], q.prototype, "mode", void 0), K([V()], q.prototype, "text", void 0), K([V()], q.prototype, "preview", void 0), K([V()], q.prototype, "op", void 0), K([V()], q.prototype, "entity", void 0), K([V()], q.prototype, "varsText", void 0), K([V()], q.prototype, "chip", void 0), K([V()], q.prototype, "when", void 0), K([V()], q.prototype, "rawText", void 0), K([V()], q.prototype, "error", void 0), K([V()], q.prototype, "busy", void 0), q = K([z("at-add-job-dialog")], q);
// src/components/history-table.ts
var qe = {
	done: "✓",
	failed: "✗",
	missed: "⚠",
	cancelled: "⊘"
}, Je = [
	"all",
	"done",
	"failed",
	"missed",
	"cancelled"
], J = class extends R {
	constructor(...e) {
		super(...e), this.history = [], this.now = Date.now(), this.filter = "all", this.editing = null, this.value = "";
	}
	fire(e, t) {
		this.dispatchEvent(new CustomEvent(e, {
			detail: t,
			bubbles: !0,
			composed: !0
		}));
	}
	submit(e) {
		if (!this.value) return;
		let t = We(this.value, this.hass?.config.time_zone ?? "UTC");
		Number.isNaN(t.getTime()) || (this.fire("reschedule-job", {
			job: e,
			due: t.toISOString()
		}), this.editing = null, this.value = "");
	}
	row(e) {
		let t = W(new Date(e.finished_at ?? e.due), new Date(this.now), this.hass?.locale?.language ?? this.hass?.language ?? "en", this.hass?.config.time_zone ?? "UTC");
		return k`<tr @click=${() => this.fire("open-job", { job: e })}>
      <td class="status ${e.status}" title=${e.status}>${qe[e.status] ?? e.status}</td>
      <td class="nowrap">${t}</td>
      <td>${e.summary}</td>
      <td class="result">${e.result.error ?? ""}</td>
      <td class="actions" @click=${(e) => e.stopPropagation()}>
        ${this.editing === e.id ? k`<input type="datetime-local" .value=${this.value} @input=${(e) => this.value = e.target.value} />
              <button @click=${() => this.submit(e)}>Save</button>
              <button @click=${() => this.editing = null}>Cancel</button>` : k`<button @click=${() => {
			this.editing = e.id, this.value = Ge(new Date(Date.now() + 36e5), this.hass?.config.time_zone ?? "UTC");
		}}>Re-schedule</button>`}
      </td>
    </tr>`;
	}
	render() {
		let e = this.filter === "all" ? this.history : this.history.filter((e) => e.status === this.filter);
		return k`
      <div class="chips">
        ${Je.map((e) => k`<button class="chip ${this.filter === e ? "on" : ""}" @click=${() => this.filter = e}>${e === "all" ? "All" : `${qe[e]} ${e}`}</button>`)}
      </div>
      ${e.length ? k`<table>
            <thead><tr><th></th><th>Time</th><th>Job</th><th>Result</th><th></th></tr></thead>
            <tbody>${e.map((e) => this.row(e))}</tbody>
          </table>` : k`<p class="empty">${this.history.length ? "No jobs match this filter." : "No history yet."}</p>`}
    `;
	}
	static {
		this.styles = o`
    .chips { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    .chip { font: inherit; color: var(--primary-text-color); background: none; border: 1px solid var(--divider-color); border-radius: 16px; padding: 4px 12px; cursor: pointer; }
    .chip.on { background: var(--primary-color); color: var(--text-primary-color, #fff); border-color: var(--primary-color); }
    table { width: 100%; border-collapse: collapse; background: var(--card-background-color); border-radius: 8px; }
    th { text-align: left; padding: 8px 12px; color: var(--secondary-text-color); font-weight: 500; }
    td { padding: 10px 12px; border-top: 1px solid var(--divider-color); }
    tr { cursor: pointer; }
    .nowrap { white-space: nowrap; }
    .status { font-size: 18px; width: 24px; }
    .status.done { color: var(--success-color, #43a047); }
    .status.failed { color: var(--error-color, #db4437); }
    .status.missed { color: var(--warning-color, #ffa600); }
    .status.cancelled { color: var(--secondary-text-color); }
    .result { color: var(--secondary-text-color); }
    .actions { text-align: right; white-space: nowrap; }
    .actions button { font: inherit; color: var(--primary-color); background: none; border: none; cursor: pointer; padding: 4px 8px; }
    .empty { color: var(--secondary-text-color); text-align: center; padding: 32px; }
  `;
	}
};
K([B({ attribute: !1 })], J.prototype, "hass", void 0), K([B({ attribute: !1 })], J.prototype, "history", void 0), K([B({ type: Number })], J.prototype, "now", void 0), K([V()], J.prototype, "filter", void 0), K([V()], J.prototype, "editing", void 0), K([V()], J.prototype, "value", void 0), J = K([z("at-history-table")], J);
// src/source.ts
function Ye(e, t) {
	let { via: n, device_id: r, user_id: i } = e.source;
	if (n === "voice" || n === "llm") {
		let e = r ? t?.devices?.[r] : void 0;
		return `🎙 ${e?.name_by_user ?? e?.name ?? "Voice"}`;
	}
	return n === "panel" || n === "todo" ? `🖱 ${i && t?.user?.id === i ? t.user.name : "User"}` : "⚙ Automation";
}
function Y(e) {
	return typeof e == "string" && /^[\w./:-]+$/.test(e) ? e : JSON.stringify(e);
}
function X(e, t = 0) {
	let n = "  ".repeat(t);
	if (Array.isArray(e)) return e.length === 0 ? `${n}[]` : e.map((e) => {
		if (typeof e == "object" && e) {
			let r = X(e, t + 1).replace(/^\s+/, "");
			return `${n}- ${r}`;
		}
		return `${n}- ${Y(e)}`;
	}).join("\n");
	if (typeof e == "object" && e) {
		let r = Object.entries(e);
		return r.length === 0 ? `${n}{}` : r.map(([e, r]) => typeof r == "object" && r && (Array.isArray(r) ? r.length : Object.keys(r).length) ? `${n}${e}:\n${X(r, t + 1)}` : `${n}${e}: ${typeof r == "object" && r ? X(r) : Y(r)}`).join("\n");
	}
	return `${n}${Y(e)}`;
}
// src/components/job-details.ts
var Z = class extends R {
	close() {
		this.dispatchEvent(new CustomEvent("close-details", {
			bubbles: !0,
			composed: !0
		}));
	}
	render() {
		let e = this.job;
		if (!e) return j;
		let t = this.hass?.config.time_zone ?? "UTC", n = this.hass?.locale?.language ?? this.hass?.language ?? "en", r = new Intl.DateTimeFormat(n, {
			timeZone: t,
			dateStyle: "medium",
			timeStyle: "medium"
		}).format(new Date(e.created_at)), i = e.intent ? `${e.intent.type}\n${X(e.intent.slots)}` : X(e.action ?? []);
		return k`<div class="backdrop" @click=${() => this.close()}>
      <div class="card" role="dialog" aria-label="Job details" @click=${(e) => e.stopPropagation()}>
        <h2>${e.summary}</h2>
        <dl>
          <dt>${e.intent ? "Intent" : "Action"}</dt>
          <dd><pre>${i}</pre></dd>
          <dt>Created by</dt>
          <dd>${Ye(e, this.hass)}</dd>
          <dt>Created</dt>
          <dd>${r}</dd>
          <dt>ID</dt>
          <dd><code>${e.id}</code></dd>
        </dl>
        <button @click=${() => this.close()}>Close</button>
      </div>
    </div>`;
	}
	static {
		this.styles = o`
    .backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 10; }
    .card { background: var(--card-background-color); color: var(--primary-text-color); border-radius: 8px; padding: 16px 24px; max-width: 560px; width: calc(100% - 32px); max-height: 80vh; overflow: auto; }
    h2 { margin-top: 0; font-weight: 400; }
    dt { color: var(--secondary-text-color); font-size: 12px; margin-top: 12px; }
    dd { margin: 2px 0 0; }
    pre { margin: 0; white-space: pre-wrap; font-family: var(--code-font-family, monospace); }
    button { font: inherit; margin-top: 16px; color: var(--primary-color); background: none; border: none; cursor: pointer; }
  `;
	}
};
K([B({ attribute: !1 })], Z.prototype, "hass", void 0), K([B({ attribute: !1 })], Z.prototype, "job", void 0), Z = K([z("at-job-details")], Z);
// src/components/upcoming-table.ts
var Q = class extends R {
	constructor(...e) {
		super(...e), this.pending = [], this.running = [], this.now = Date.now(), this.isAdmin = !1;
	}
	fire(e, t, n) {
		n?.stopPropagation(), this.dispatchEvent(new CustomEvent(e, {
			detail: { job: t },
			bubbles: !0,
			composed: !0
		}));
	}
	when(e) {
		let t = new Date(e.due);
		return He(t.getTime(), this.now) || W(t, new Date(this.now), this.hass?.locale?.language ?? this.hass?.language ?? "en", this.hass?.config.time_zone ?? "UTC");
	}
	row(e, t) {
		let n = !t && (this.isAdmin || !e.raw_action);
		return k`<tr @click=${() => this.fire("open-job", e)}>
      <td class="when">${t ? "Running…" : this.when(e)}</td>
      <td>${e.summary}</td>
      <td>${Ye(e, this.hass)}</td>
      <td class="actions">
        ${t ? j : k`${n ? k`<button title="Run now" aria-label="Run now" @click=${(t) => this.fire("run-job", e, t)}>▶</button>` : j}
            <button title="Cancel" aria-label="Cancel" @click=${(t) => this.fire("cancel-job", e, t)}>✕</button>`}
      </td>
    </tr>`;
	}
	render() {
		return !this.pending.length && !this.running.length ? k`<p class="empty">Nothing scheduled.</p>` : k`<table>
      <thead><tr><th>When</th><th>Job</th><th>Source</th><th></th></tr></thead>
      <tbody>
        ${this.running.map((e) => this.row(e, !0))} ${this.pending.map((e) => this.row(e, !1))}
      </tbody>
    </table>`;
	}
	static {
		this.styles = o`
    table { width: 100%; border-collapse: collapse; background: var(--card-background-color); border-radius: 8px; }
    th { text-align: left; padding: 8px 12px; color: var(--secondary-text-color); font-weight: 500; }
    td { padding: 10px 12px; border-top: 1px solid var(--divider-color); }
    tr { cursor: pointer; }
    tbody tr:hover { background: var(--secondary-background-color); }
    .when { font-variant-numeric: tabular-nums; white-space: nowrap; }
    .actions { text-align: right; white-space: nowrap; }
    button { font: inherit; color: var(--primary-text-color); background: none; border: none; cursor: pointer; padding: 4px 8px; }
    .empty { color: var(--secondary-text-color); text-align: center; padding: 32px; }
  `;
	}
};
K([B({ attribute: !1 })], Q.prototype, "hass", void 0), K([B({ attribute: !1 })], Q.prototype, "pending", void 0), K([B({ attribute: !1 })], Q.prototype, "running", void 0), K([B({ type: Number })], Q.prototype, "now", void 0), K([B({ type: Boolean })], Q.prototype, "isAdmin", void 0), Q = K([z("at-upcoming-table")], Q);
// src/reconnect.ts
var Xe = 1e3, Ze = 3e4;
function Qe(e) {
	return Math.min(Xe * 2 ** Math.min(e, 10), Ze);
}
// src/state.ts
var $e = (e, t) => Date.parse(e.due) - Date.parse(t.due), et = (e) => Date.parse(e.finished_at ?? e.due), tt = (e, t) => et(t) - et(e);
function nt(e) {
	return {
		pending: [...e.pending].sort($e),
		running: [...e.running].sort($e),
		history: [...e.history].sort(tt)
	};
}
function rt(e, t) {
	let { job: n } = t, r = (e) => e.filter((e) => e.id !== n.id), i = {
		pending: r(e.pending),
		running: r(e.running),
		history: r(e.history)
	};
	return t.kind !== "removed" && (n.status === "pending" ? i.pending.push(n) : n.status === "running" ? i.running.push(n) : i.history.push(n)), nt(i);
}
function it(e) {
	return `Upcoming (${e.pending.length})`;
}
// src/at-panel.ts
var at = "Scheduled Jobs", $ = class extends R {
	constructor(...e) {
		super(...e), this.narrow = !1, this.tab = "upcoming", this.menuOpen = !1, this.data = {
			pending: [],
			running: [],
			history: []
		}, this.now = Date.now(), this.reconnecting = !0, this.error = "", this.confirmCancelAll = !1, this.addOpen = !1, this.attempt = 0, this.subscribed = !1, this.gone = !1, this.generation = 0, this.onRun = (e) => {
			let t = this.hass;
			t && this.call(() => Ne(t, e.detail.job.id));
		}, this.onCancel = (e) => {
			let t = this.hass;
			t && this.call(() => Me(t, [e.detail.job.id]));
		}, this.onReschedule = (e) => {
			let t = this.hass;
			t && this.call(() => Pe(t, e.detail.job.id, e.detail.due));
		}, this.onOpen = (e) => this.details = e.detail.job;
	}
	connectedCallback() {
		super.connectedCallback(), this.gone = !1, this.generation++, window.clearInterval(this.tick), this.tick = window.setInterval(() => this.now = Date.now(), 1e3), this.hass && this.start();
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this.gone = !0, this.generation++, window.clearInterval(this.tick), window.clearTimeout(this.retryTimer), this.subscribed = !1, this.unsub?.().catch(() => void 0), this.unsub = void 0;
	}
	updated(e) {
		e.has("hass") && this.hass && !this.subscribed && !this.gone && this.start();
	}
	async start() {
		this.hass && !this.subscribed && (this.subscribed = !0, Ie(this.hass).then((e) => this.atInfo = e, () => void 0), await this.subscribe());
	}
	async subscribe() {
		if (!this.hass || this.gone) return;
		let e = this.generation;
		try {
			let t = await ke(this.hass, (t) => {
				e === this.generation && this.onEvent(t);
			});
			if (e !== this.generation) {
				t().catch(() => void 0);
				return;
			}
			this.unsub = t;
		} catch {
			e === this.generation && this.scheduleRetry();
		}
	}
	onEvent(e) {
		if ("snapshot" in e) this.data = nt(e.snapshot), this.reconnecting = !1, this.attempt = 0;
		else if ("change" in e) this.data = rt(this.data, e.change);
		else if ("stopped" in e) {
			let e = this.unsub;
			this.unsub = void 0, e?.().catch(() => void 0), this.scheduleRetry();
		}
	}
	scheduleRetry() {
		if (this.reconnecting = !0, this.gone) return;
		let e = Qe(this.attempt++);
		window.clearTimeout(this.retryTimer), this.retryTimer = window.setTimeout(() => void this.subscribe(), e);
	}
	async call(e) {
		try {
			await e();
		} catch (e) {
			let t = e?.message;
			this.error = t || "Request failed";
		}
	}
	cancelAll() {
		let e = this.hass;
		if (!e) return;
		if (!this.confirmCancelAll) {
			this.confirmCancelAll = !0;
			return;
		}
		this.confirmCancelAll = !1, this.menuOpen = !1;
		let t = this.data.pending.map((e) => e.id);
		t.length && this.call(() => Me(e, t));
	}
	clearHistory() {
		let e = this.hass;
		this.menuOpen = !1, this.confirmCancelAll = !1, e && this.call(() => Fe(e));
	}
	toggleMenu() {
		this.menuOpen = !this.menuOpen, this.confirmCancelAll = !1;
	}
	fire_toggle_menu() {
		this.dispatchEvent(new Event("hass-toggle-menu", {
			bubbles: !0,
			composed: !0
		}));
	}
	get title_() {
		let e = this.panel?.config?.title;
		return typeof e == "string" && e ? e : at;
	}
	tabButton(e, t) {
		return k`<button
      class="tab ${this.tab === e ? "active" : ""}"
      role="tab"
      aria-selected=${this.tab === e}
      @click=${() => this.tab = e}
    >
      ${t}
    </button>`;
	}
	render() {
		return k`
      <header>
        ${this.narrow ? k`<button class="sidebar-toggle" aria-label="Open sidebar" @click=${() => this.fire_toggle_menu()}>☰</button>` : j}
        <h1>${this.title_}</h1>
        <div class="tabs" role="tablist">${this.tabButton("upcoming", it(this.data))} ${this.tabButton("history", "History")}</div>
        <button class="add" @click=${() => this.addOpen = !0}>+ Add job</button>
        <div class="menu-wrap">
          <button class="menu" aria-label="More options" @click=${() => this.toggleMenu()}>⋮</button>
          ${this.menuOpen ? k`<div class="menu-pop" role="menu">
                <button role="menuitem" @click=${() => this.cancelAll()}>${this.confirmCancelAll ? "Confirm cancel all?" : "Cancel all"}</button>
                <button role="menuitem" @click=${() => this.clearHistory()}>Clear history</button>
              </div>` : j}
        </div>
      </header>
      ${this.reconnecting ? k`<div class="notice">Reconnecting…</div>` : j}
      ${this.error ? k`<div class="error" role="alert">${this.error}<button aria-label="Dismiss" @click=${() => this.error = ""}>✕</button></div>` : j}
      <main @run-job=${this.onRun} @cancel-job=${this.onCancel} @reschedule-job=${this.onReschedule} @open-job=${this.onOpen}>
        ${this.tab === "upcoming" ? k`<at-upcoming-table
              .hass=${this.hass}
              .pending=${this.data.pending}
              .running=${this.data.running}
              .now=${this.now}
              .isAdmin=${this.atInfo?.is_admin ?? !1}
            ></at-upcoming-table>` : k`<at-history-table .hass=${this.hass} .history=${this.data.history} .now=${this.now}></at-history-table>`}
      </main>
      <at-add-job-dialog
        .hass=${this.hass}
        .isAdmin=${this.atInfo?.is_admin ?? !1}
        .open=${this.addOpen}
        @close-add-job=${() => this.addOpen = !1}
      ></at-add-job-dialog>
      <at-job-details .hass=${this.hass} .job=${this.details} @close-details=${() => this.details = void 0}></at-job-details>
    `;
	}
	static {
		this.styles = o`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
    header {
      display: flex;
      align-items: center;
      gap: 12px;
      box-sizing: border-box;
      min-height: var(--header-height, 56px);
      padding: 0 16px;
      position: sticky;
      top: 0;
      z-index: 4;
      background: var(--app-header-background-color, var(--card-background-color));
      color: var(--app-header-text-color, var(--primary-text-color));
      border-bottom: 1px solid var(--divider-color);
    }
    h1 {
      margin: 0;
      font-size: var(--ha-font-size-xl, 20px);
      font-weight: var(--ha-font-weight-normal, 400);
      flex: 1;
    }
    .sidebar-toggle {
      font-size: 24px;
      padding: 8px;
      margin-left: -8px;
      color: inherit;
    }
    button {
      font: inherit;
      color: var(--primary-text-color);
      background: none;
      border: none;
      cursor: pointer;
    }
    .tabs {
      display: flex;
      gap: 4px;
    }
    .tab {
      padding: 10px 14px;
      border-bottom: 2px solid transparent;
    }
    .tab.active {
      color: var(--primary-color);
      border-bottom-color: var(--primary-color);
    }
    .add {
      padding: 8px 14px;
      border-radius: 18px;
      color: var(--text-primary-color, #fff);
      background: var(--primary-color);
    }
    .menu-wrap {
      position: relative;
    }
    .menu {
      font-size: 20px;
      padding: 4px 8px;
    }
    .menu-pop {
      position: absolute;
      right: 0;
      top: 100%;
      min-width: 160px;
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 4px;
    }
    main {
      padding: 16px;
    }
    .menu-pop button {
      display: block;
      width: 100%;
      text-align: left;
      padding: 10px 14px;
    }
    .notice {
      margin: 8px 16px 0;
      padding: 6px 12px;
      font-size: 13px;
      color: var(--secondary-text-color);
    }
    .error {
      display: flex;
      justify-content: space-between;
      margin: 8px 16px 0;
      padding: 8px 12px;
      border-radius: 4px;
      color: #fff;
      background: var(--error-color, #db4437);
    }
    .error button {
      color: inherit;
    }
    @media (max-width: 600px) {
      header {
        flex-wrap: wrap;
      }
    }
  `;
	}
};
K([B({ attribute: !1 })], $.prototype, "hass", void 0), K([B({ type: Boolean })], $.prototype, "narrow", void 0), K([B({ attribute: !1 })], $.prototype, "panel", void 0), K([B({ attribute: !1 })], $.prototype, "route", void 0), K([V()], $.prototype, "tab", void 0), K([V()], $.prototype, "menuOpen", void 0), K([V()], $.prototype, "data", void 0), K([V()], $.prototype, "now", void 0), K([V()], $.prototype, "reconnecting", void 0), K([V()], $.prototype, "error", void 0), K([V()], $.prototype, "confirmCancelAll", void 0), K([V()], $.prototype, "details", void 0), K([V()], $.prototype, "atInfo", void 0), K([V()], $.prototype, "addOpen", void 0), $ = K([z("at-panel")], $);
export { $ as AtPanel };
