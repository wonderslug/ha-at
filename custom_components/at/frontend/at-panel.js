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
}, h = (e, t) => !l(e, t), g = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	useDefault: !1,
	hasChanged: h
};
Symbol.metadata ??= Symbol("metadata"), f.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var _ = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = g) {
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
		return this.elementProperties.get(e) ?? g;
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
_.elementStyles = [], _.shadowRootOptions = { mode: "open" }, _[p("elementProperties")] = /* @__PURE__ */ new Map(), _[p("finalized")] = /* @__PURE__ */ new Map(), ae?.({ ReactiveElement: _ }), (f.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var v = globalThis, oe = (e) => e, y = v.trustedTypes, se = y ? y.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, ce = "$lit$", b = `lit$${Math.random().toFixed(9).slice(2)}$`, le = "?" + b, ue = `<${le}>`, x = document, S = () => x.createComment(""), C = (e) => e === null || typeof e != "object" && typeof e != "function", w = Array.isArray, de = (e) => w(e) || typeof e?.[Symbol.iterator] == "function", T = "[ 	\n\f\r]", E = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, fe = /-->/g, D = />/g, O = RegExp(`>|${T}(?:([^\\s"'>=/]+)(${T}*=${T}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), k = /'/g, A = /"/g, j = /^(?:script|style|textarea|title)$/i, M = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), N = Symbol.for("lit-noChange"), P = Symbol.for("lit-nothing"), F = /* @__PURE__ */ new WeakMap(), I = x.createTreeWalker(x, 129);
function pe(e, t) {
	if (!w(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return se === void 0 ? t : se.createHTML(t);
}
var me = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = E;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === E ? c[1] === "!--" ? o = fe : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = O) : (j.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = O) : o = D : o === O ? c[0] === ">" ? (o = i ?? E, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? O : c[3] === "\"" ? A : k) : o === A || o === k ? o = O : o === fe || o === D ? o = E : (o = O, i = void 0);
		let d = o === O && e[t + 1].startsWith("/>") ? " " : "";
		a += o === E ? n + ue : l >= 0 ? (r.push(s), n.slice(0, l) + ce + n.slice(l) + b + d) : n + b + (l === -2 ? t : d);
	}
	return [pe(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, L = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = me(t, n);
		if (this.el = e.createElement(l, r), I.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = I.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(ce)) {
					let t = u[o++], n = i.getAttribute(e).split(b), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? ge : r[1] === "?" ? _e : r[1] === "@" ? ve : B
					}), i.removeAttribute(e);
				} else e.startsWith(b) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (j.test(i.tagName)) {
					let e = i.textContent.split(b), t = e.length - 1;
					if (t > 0) {
						i.textContent = y ? y.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], S()), I.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], S());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === le) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(b, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += b.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = x.createElement("template");
		return n.innerHTML = e, n;
	}
};
function R(e, t, n = e, r) {
	if (t === N) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = C(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = R(e, i._$AS(e, t.values), i, r)), t;
}
var he = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? x).importNode(t, !0);
		I.currentNode = r;
		let i = I.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new z(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new ye(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = I.nextNode(), a++);
		}
		return I.currentNode = x, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, z = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = P, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = R(this, e, t), C(e) ? e === P || e == null || e === "" ? (this._$AH !== P && this._$AR(), this._$AH = P) : e !== this._$AH && e !== N && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? de(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== P && C(this._$AH) ? this._$AA.nextSibling.data = e : this.T(x.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = L.createElement(pe(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new he(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = F.get(e.strings);
		return t === void 0 && F.set(e.strings, t = new L(e)), t;
	}
	k(t) {
		w(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(S()), this.O(S()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = oe(e).nextSibling;
			oe(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, B = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = P, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = P;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = R(this, e, t, 0), a = !C(e) || e !== this._$AH && e !== N, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = R(this, r[n + o], t, o), s === N && (s = this._$AH[o]), a ||= !C(s) || s !== this._$AH[o], s === P ? e = P : e !== P && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === P ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, ge = class extends B {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === P ? void 0 : e;
	}
}, _e = class extends B {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== P);
	}
}, ve = class extends B {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = R(this, e, t, 0) ?? P) === N) return;
		let n = this._$AH, r = e === P && n !== P || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== P && (n === P || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, ye = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		R(this, e);
	}
}, be = v.litHtmlPolyfillSupport;
be?.(L, z), (v.litHtmlVersions ??= []).push("3.3.3");
var xe = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new z(t.insertBefore(S(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, V = globalThis, H = class extends _ {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = xe(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return N;
	}
};
H._$litElement$ = !0, H.finalized = !0, V.litElementHydrateSupport?.({ LitElement: H });
var Se = V.litElementPolyfillSupport;
Se?.({ LitElement: H }), (V.litElementVersions ??= []).push("4.2.2");
// node_modules/@lit/reactive-element/decorators/custom-element.js
var U = (e) => (t, n) => {
	n === void 0 ? customElements.define(e, t) : n.addInitializer(() => {
		customElements.define(e, t);
	});
}, Ce = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	hasChanged: h
}, we = (e = Ce, t, n) => {
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
function W(e) {
	return (t, n) => typeof n == "object" ? we(e, t, n) : ((e, t, n) => {
		let r = t.hasOwnProperty(n);
		return t.constructor.createProperty(n, e), r ? Object.getOwnPropertyDescriptor(t, n) : void 0;
	})(e, t, n);
}
// node_modules/@lit/reactive-element/decorators/state.js
function G(e) {
	return W({
		...e,
		state: !0,
		attribute: !1
	});
}
// src/api.ts
function Te(e, t) {
	return e.connection.subscribeMessage(t, { type: "at/subscribe" });
}
function Ee(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/cancel",
		job_ids: t
	});
}
function De(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/run_now",
		job_id: t
	});
}
function Oe(e, t, n) {
	return e.connection.sendMessagePromise({
		type: "at/reschedule",
		job_id: t,
		due: n
	});
}
function ke(e) {
	return e.connection.sendMessagePromise({ type: "at/clear_history" });
}
function Ae(e) {
	return e.connection.sendMessagePromise({ type: "at/info" });
}
// src/format.ts
var je = 36e5, Me = 864e5;
function Ne(e, t) {
	let n = e - t;
	if (n < 0 || n >= je) return "";
	let r = Math.floor(n / 1e3), i = Math.floor(r / 60), a = r % 60;
	return `${String(i).padStart(2, "0")}:${String(a).padStart(2, "0")}`;
}
function Pe(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		timeZone: n,
		year: "numeric",
		month: "numeric",
		day: "numeric"
	}).format(e);
}
function Fe(e, t, n, r) {
	let i = new Intl.DateTimeFormat(n, {
		timeZone: r,
		hour: "numeric",
		minute: "2-digit"
	}).format(e);
	if (Pe(e, n, r) === Pe(t, n, r)) return i;
	let a = e.getTime() - t.getTime();
	return a > 0 && a < 7 * Me ? `${new Intl.DateTimeFormat(n, {
		timeZone: r,
		weekday: "short"
	}).format(e)} ${i}` : `${new Intl.DateTimeFormat(n, {
		timeZone: r,
		month: "short",
		day: "numeric"
	}).format(e)}, ${i}`;
}
function K(e, t) {
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
function Ie(e, t) {
	let n = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(e);
	if (!n) return /* @__PURE__ */ new Date(NaN);
	let r = Date.UTC(+n[1], n[2] - 1, +n[3], +n[4], +n[5]), i = r - K(r, t);
	return i = r - K(i, t), new Date(i);
}
function Le(e, t) {
	return new Date(e.getTime() + K(e.getTime(), t)).toISOString().slice(0, 16);
}
// \0@oxc-project+runtime@0.156.0/helpers/esm/decorate.js
function q(e, t, n, r) {
	var i = arguments.length, a = i < 3 ? t : r === null ? r = Object.getOwnPropertyDescriptor(t, n) : r, o;
	if (typeof Reflect == "object" && typeof Reflect.decorate == "function") a = Reflect.decorate(e, t, n, r);
	else for (var s = e.length - 1; s >= 0; s--) (o = e[s]) && (a = (i < 3 ? o(a) : i > 3 ? o(t, n, a) : o(t, n)) || a);
	return i > 3 && a && Object.defineProperty(t, n, a), a;
}
// src/components/history-table.ts
var Re = {
	done: "✓",
	failed: "✗",
	missed: "⚠",
	cancelled: "⊘"
}, ze = [
	"all",
	"done",
	"failed",
	"missed",
	"cancelled"
], J = class extends H {
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
		let t = Ie(this.value, this.hass?.config.time_zone ?? "UTC");
		Number.isNaN(t.getTime()) || (this.fire("reschedule-job", {
			job: e,
			due: t.toISOString()
		}), this.editing = null, this.value = "");
	}
	row(e) {
		let t = Fe(new Date(e.finished_at ?? e.due), new Date(this.now), this.hass?.locale?.language ?? this.hass?.language ?? "en", this.hass?.config.time_zone ?? "UTC");
		return M`<tr @click=${() => this.fire("open-job", { job: e })}>
      <td class="status ${e.status}" title=${e.status}>${Re[e.status] ?? e.status}</td>
      <td class="nowrap">${t}</td>
      <td>${e.summary}</td>
      <td class="result">${e.result.error ?? ""}</td>
      <td class="actions" @click=${(e) => e.stopPropagation()}>
        ${this.editing === e.id ? M`<input type="datetime-local" .value=${this.value} @input=${(e) => this.value = e.target.value} />
              <button @click=${() => this.submit(e)}>Save</button>
              <button @click=${() => this.editing = null}>Cancel</button>` : M`<button @click=${() => {
			this.editing = e.id, this.value = Le(new Date(Date.now() + 36e5), this.hass?.config.time_zone ?? "UTC");
		}}>Re-schedule</button>`}
      </td>
    </tr>`;
	}
	render() {
		let e = this.filter === "all" ? this.history : this.history.filter((e) => e.status === this.filter);
		return M`
      <div class="chips">
        ${ze.map((e) => M`<button class="chip ${this.filter === e ? "on" : ""}" @click=${() => this.filter = e}>${e === "all" ? "All" : `${Re[e]} ${e}`}</button>`)}
      </div>
      ${e.length ? M`<table>
            <thead><tr><th></th><th>Time</th><th>Job</th><th>Result</th><th></th></tr></thead>
            <tbody>${e.map((e) => this.row(e))}</tbody>
          </table>` : M`<p class="empty">${this.history.length ? "No jobs match this filter." : "No history yet."}</p>`}
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
q([W({ attribute: !1 })], J.prototype, "hass", void 0), q([W({ attribute: !1 })], J.prototype, "history", void 0), q([W({ type: Number })], J.prototype, "now", void 0), q([G()], J.prototype, "filter", void 0), q([G()], J.prototype, "editing", void 0), q([G()], J.prototype, "value", void 0), J = q([U("at-history-table")], J);
// src/source.ts
function Be(e, t) {
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
var Z = class extends H {
	close() {
		this.dispatchEvent(new CustomEvent("close-details", {
			bubbles: !0,
			composed: !0
		}));
	}
	render() {
		let e = this.job;
		if (!e) return P;
		let t = this.hass?.config.time_zone ?? "UTC", n = this.hass?.locale?.language ?? this.hass?.language ?? "en", r = new Intl.DateTimeFormat(n, {
			timeZone: t,
			dateStyle: "medium",
			timeStyle: "medium"
		}).format(new Date(e.created_at)), i = e.intent ? `${e.intent.type}\n${X(e.intent.slots)}` : X(e.action ?? []);
		return M`<div class="backdrop" @click=${() => this.close()}>
      <div class="card" role="dialog" aria-label="Job details" @click=${(e) => e.stopPropagation()}>
        <h2>${e.summary}</h2>
        <dl>
          <dt>${e.intent ? "Intent" : "Action"}</dt>
          <dd><pre>${i}</pre></dd>
          <dt>Created by</dt>
          <dd>${Be(e, this.hass)}</dd>
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
q([W({ attribute: !1 })], Z.prototype, "hass", void 0), q([W({ attribute: !1 })], Z.prototype, "job", void 0), Z = q([U("at-job-details")], Z);
// src/components/upcoming-table.ts
var Q = class extends H {
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
		return Ne(t.getTime(), this.now) || Fe(t, new Date(this.now), this.hass?.locale?.language ?? this.hass?.language ?? "en", this.hass?.config.time_zone ?? "UTC");
	}
	row(e, t) {
		let n = !t && (this.isAdmin || !e.raw_action);
		return M`<tr @click=${() => this.fire("open-job", e)}>
      <td class="when">${t ? "Running…" : this.when(e)}</td>
      <td>${e.summary}</td>
      <td>${Be(e, this.hass)}</td>
      <td class="actions">
        ${t ? P : M`${n ? M`<button title="Run now" aria-label="Run now" @click=${(t) => this.fire("run-job", e, t)}>▶</button>` : P}
            <button title="Cancel" aria-label="Cancel" @click=${(t) => this.fire("cancel-job", e, t)}>✕</button>`}
      </td>
    </tr>`;
	}
	render() {
		return !this.pending.length && !this.running.length ? M`<p class="empty">Nothing scheduled.</p>` : M`<table>
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
q([W({ attribute: !1 })], Q.prototype, "hass", void 0), q([W({ attribute: !1 })], Q.prototype, "pending", void 0), q([W({ attribute: !1 })], Q.prototype, "running", void 0), q([W({ type: Number })], Q.prototype, "now", void 0), q([W({ type: Boolean })], Q.prototype, "isAdmin", void 0), Q = q([U("at-upcoming-table")], Q);
// src/reconnect.ts
var Ve = 1e3, He = 3e4;
function Ue(e) {
	return Math.min(Ve * 2 ** Math.min(e, 10), He);
}
// src/state.ts
var We = (e, t) => Date.parse(e.due) - Date.parse(t.due), Ge = (e) => Date.parse(e.finished_at ?? e.due), Ke = (e, t) => Ge(t) - Ge(e);
function qe(e) {
	return {
		pending: [...e.pending].sort(We),
		running: [...e.running].sort(We),
		history: [...e.history].sort(Ke)
	};
}
function Je(e, t) {
	let { job: n } = t, r = (e) => e.filter((e) => e.id !== n.id), i = {
		pending: r(e.pending),
		running: r(e.running),
		history: r(e.history)
	};
	return t.kind !== "removed" && (n.status === "pending" ? i.pending.push(n) : n.status === "running" ? i.running.push(n) : i.history.push(n)), qe(i);
}
// src/at-panel.ts
var Ye = "at", $ = class extends H {
	constructor(...e) {
		super(...e), this.narrow = !1, this.tab = "upcoming", this.menuOpen = !1, this.data = {
			pending: [],
			running: [],
			history: []
		}, this.now = Date.now(), this.reconnecting = !0, this.error = "", this.confirmCancelAll = !1, this.attempt = 0, this.subscribed = !1, this.gone = !1, this.generation = 0, this.onRun = (e) => {
			let t = this.hass;
			t && this.call(() => De(t, e.detail.job.id));
		}, this.onCancel = (e) => {
			let t = this.hass;
			t && this.call(() => Ee(t, [e.detail.job.id]));
		}, this.onReschedule = (e) => {
			let t = this.hass;
			t && this.call(() => Oe(t, e.detail.job.id, e.detail.due));
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
		this.hass && !this.subscribed && (this.subscribed = !0, Ae(this.hass).then((e) => this.atInfo = e, () => void 0), await this.subscribe());
	}
	async subscribe() {
		if (!this.hass || this.gone) return;
		let e = this.generation;
		try {
			let t = await Te(this.hass, (t) => {
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
		if ("snapshot" in e) this.data = qe(e.snapshot), this.reconnecting = !1, this.attempt = 0;
		else if ("change" in e) this.data = Je(this.data, e.change);
		else if ("stopped" in e) {
			let e = this.unsub;
			this.unsub = void 0, e?.().catch(() => void 0), this.scheduleRetry();
		}
	}
	scheduleRetry() {
		if (this.reconnecting = !0, this.gone) return;
		let e = Ue(this.attempt++);
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
		t.length && this.call(() => Ee(e, t));
	}
	clearHistory() {
		let e = this.hass;
		this.menuOpen = !1, this.confirmCancelAll = !1, e && this.call(() => ke(e));
	}
	toggleMenu() {
		this.menuOpen = !this.menuOpen, this.confirmCancelAll = !1;
	}
	get title_() {
		let e = this.panel?.config?.title;
		return typeof e == "string" && e ? e : Ye;
	}
	tabButton(e, t) {
		return M`<button
      class="tab ${this.tab === e ? "active" : ""}"
      role="tab"
      aria-selected=${this.tab === e}
      @click=${() => this.tab = e}
    >
      ${t}
    </button>`;
	}
	render() {
		return M`
      <header>
        <h1>${this.title_}</h1>
        <div class="tabs" role="tablist">${this.tabButton("upcoming", "Upcoming")} ${this.tabButton("history", "History")}</div>
        <button class="add">+ Add job</button>
        <div class="menu-wrap">
          <button class="menu" aria-label="More options" @click=${() => this.toggleMenu()}>⋮</button>
          ${this.menuOpen ? M`<div class="menu-pop" role="menu">
                <button role="menuitem" @click=${() => this.cancelAll()}>${this.confirmCancelAll ? "Confirm cancel all?" : "Cancel all"}</button>
                <button role="menuitem" @click=${() => this.clearHistory()}>Clear history</button>
              </div>` : P}
        </div>
      </header>
      ${this.reconnecting ? M`<div class="notice">Reconnecting…</div>` : P}
      ${this.error ? M`<div class="error" role="alert">${this.error}<button aria-label="Dismiss" @click=${() => this.error = ""}>✕</button></div>` : P}
      <main @run-job=${this.onRun} @cancel-job=${this.onCancel} @reschedule-job=${this.onReschedule} @open-job=${this.onOpen}>
        ${this.tab === "upcoming" ? M`<at-upcoming-table
              .hass=${this.hass}
              .pending=${this.data.pending}
              .running=${this.data.running}
              .now=${this.now}
              .isAdmin=${this.atInfo?.is_admin ?? !1}
            ></at-upcoming-table>` : M`<at-history-table .hass=${this.hass} .history=${this.data.history} .now=${this.now}></at-history-table>`}
      </main>
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
      padding: 8px 16px;
      background: var(--card-background-color);
      border-bottom: 1px solid var(--divider-color);
    }
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 400;
      flex: 1;
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
q([W({ attribute: !1 })], $.prototype, "hass", void 0), q([W({ type: Boolean })], $.prototype, "narrow", void 0), q([W({ attribute: !1 })], $.prototype, "panel", void 0), q([W({ attribute: !1 })], $.prototype, "route", void 0), q([G()], $.prototype, "tab", void 0), q([G()], $.prototype, "menuOpen", void 0), q([G()], $.prototype, "data", void 0), q([G()], $.prototype, "now", void 0), q([G()], $.prototype, "reconnecting", void 0), q([G()], $.prototype, "error", void 0), q([G()], $.prototype, "confirmCancelAll", void 0), q([G()], $.prototype, "details", void 0), q([G()], $.prototype, "atInfo", void 0), $ = q([U("at-panel")], $);
export { $ as AtPanel };
