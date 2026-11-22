// node_modules/@mdi/js/mdi.js
var e = "M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z", t = "M12 2C17.5 2 22 6.5 22 12S17.5 22 12 22 2 17.5 2 12 6.5 2 12 2M12 4C10.1 4 8.4 4.6 7.1 5.7L18.3 16.9C19.3 15.5 20 13.8 20 12C20 7.6 16.4 4 12 4M16.9 18.3L5.7 7.1C4.6 8.4 4 10.1 4 12C4 16.4 7.6 20 12 20C13.9 20 15.6 19.4 16.9 18.3Z", n = "M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z", r = "M20 12H22V18H20V12M20 20H22V22H20V20M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22C14.3 22 16.3 21.2 18 20V10H21.8C20.9 5.4 16.8 2 12 2M16.2 16.2L11 13V7H12.5V12.2L17 14.9L16.2 16.2Z", i = globalThis, a = i.ShadowRoot && (i.ShadyCSS === void 0 || i.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, o = Symbol(), s = /* @__PURE__ */ new WeakMap(), c = class {
	constructor(e, t, n) {
		if (this._$cssResult$ = !0, n !== o) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
		this.cssText = e, this.t = t;
	}
	get styleSheet() {
		let e = this.o, t = this.t;
		if (a && e === void 0) {
			let n = t !== void 0 && t.length === 1;
			n && (e = s.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), n && s.set(t, e));
		}
		return e;
	}
	toString() {
		return this.cssText;
	}
}, l = (e) => new c(typeof e == "string" ? e : e + "", void 0, o), u = (e, ...t) => new c(e.length === 1 ? e[0] : t.reduce((t, n, r) => t + ((e) => {
	if (!0 === e._$cssResult$) return e.cssText;
	if (typeof e == "number") return e;
	throw Error("Value passed to 'css' function must be a 'css' function result: " + e + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
})(n) + e[r + 1], e[0]), e, o), d = (e, t) => {
	if (a) e.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
	else for (let n of t) {
		let t = document.createElement("style"), r = i.litNonce;
		r !== void 0 && t.setAttribute("nonce", r), t.textContent = n.cssText, e.appendChild(t);
	}
}, ee = a ? (e) => e : (e) => e instanceof CSSStyleSheet ? ((e) => {
	let t = "";
	for (let n of e.cssRules) t += n.cssText;
	return l(t);
})(e) : e, { is: te, defineProperty: ne, getOwnPropertyDescriptor: re, getOwnPropertyNames: ie, getOwnPropertySymbols: ae, getPrototypeOf: oe } = Object, f = globalThis, se = f.trustedTypes, ce = se ? se.emptyScript : "", le = f.reactiveElementPolyfillSupport, p = (e, t) => e, m = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? ce : null;
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
}, ue = (e, t) => !te(e, t), de = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	useDefault: !1,
	hasChanged: ue
};
Symbol.metadata ??= Symbol("metadata"), f.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var h = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = de) {
		if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
			let n = Symbol(), r = this.getPropertyDescriptor(e, n, t);
			r !== void 0 && ne(this.prototype, e, r);
		}
	}
	static getPropertyDescriptor(e, t, n) {
		let { get: r, set: i } = re(this.prototype, e) ?? {
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
		return this.elementProperties.get(e) ?? de;
	}
	static _$Ei() {
		if (this.hasOwnProperty(p("elementProperties"))) return;
		let e = oe(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(p("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(p("properties"))) {
			let e = this.properties, t = [...ie(e), ...ae(e)];
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
			for (let e of n) t.unshift(ee(e));
		} else e !== void 0 && t.push(ee(e));
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
		return d(e, this.constructor.elementStyles), e;
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
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? ue)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
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
h.elementStyles = [], h.shadowRootOptions = { mode: "open" }, h[p("elementProperties")] = /* @__PURE__ */ new Map(), h[p("finalized")] = /* @__PURE__ */ new Map(), le?.({ ReactiveElement: h }), (f.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var g = globalThis, fe = (e) => e, _ = g.trustedTypes, pe = _ ? _.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, me = "$lit$", v = `lit$${Math.random().toFixed(9).slice(2)}$`, he = "?" + v, ge = `<${he}>`, y = document, b = () => y.createComment(""), x = (e) => e === null || typeof e != "object" && typeof e != "function", S = Array.isArray, _e = (e) => S(e) || typeof e?.[Symbol.iterator] == "function", C = "[ 	\n\f\r]", w = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ve = /-->/g, ye = />/g, T = RegExp(`>|${C}(?:([^\\s"'>=/]+)(${C}*=${C}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), be = /'/g, xe = /"/g, Se = /^(?:script|style|textarea|title)$/i, E = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), D = Symbol.for("lit-noChange"), O = Symbol.for("lit-nothing"), Ce = /* @__PURE__ */ new WeakMap(), k = y.createTreeWalker(y, 129);
function we(e, t) {
	if (!S(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return pe === void 0 ? t : pe.createHTML(t);
}
var Te = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = w;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === w ? c[1] === "!--" ? o = ve : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = T) : (Se.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = T) : o = ye : o === T ? c[0] === ">" ? (o = i ?? w, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? T : c[3] === "\"" ? xe : be) : o === xe || o === be ? o = T : o === ve || o === ye ? o = w : (o = T, i = void 0);
		let d = o === T && e[t + 1].startsWith("/>") ? " " : "";
		a += o === w ? n + ge : l >= 0 ? (r.push(s), n.slice(0, l) + me + n.slice(l) + v + d) : n + v + (l === -2 ? t : d);
	}
	return [we(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, A = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = Te(t, n);
		if (this.el = e.createElement(l, r), k.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = k.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(me)) {
					let t = u[o++], n = i.getAttribute(e).split(v), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? De : r[1] === "?" ? Oe : r[1] === "@" ? ke : N
					}), i.removeAttribute(e);
				} else e.startsWith(v) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (Se.test(i.tagName)) {
					let e = i.textContent.split(v), t = e.length - 1;
					if (t > 0) {
						i.textContent = _ ? _.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], b()), k.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], b());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === he) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(v, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += v.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = y.createElement("template");
		return n.innerHTML = e, n;
	}
};
function j(e, t, n = e, r) {
	if (t === D) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = x(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = j(e, i._$AS(e, t.values), i, r)), t;
}
var Ee = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? y).importNode(t, !0);
		k.currentNode = r;
		let i = k.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new M(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Ae(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = k.nextNode(), a++);
		}
		return k.currentNode = y, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, M = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = O, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = j(this, e, t), x(e) ? e === O || e == null || e === "" ? (this._$AH !== O && this._$AR(), this._$AH = O) : e !== this._$AH && e !== D && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? _e(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== O && x(this._$AH) ? this._$AA.nextSibling.data = e : this.T(y.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = A.createElement(we(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new Ee(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = Ce.get(e.strings);
		return t === void 0 && Ce.set(e.strings, t = new A(e)), t;
	}
	k(t) {
		S(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(b()), this.O(b()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = fe(e).nextSibling;
			fe(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, N = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = O, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = O;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = j(this, e, t, 0), a = !x(e) || e !== this._$AH && e !== D, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = j(this, r[n + o], t, o), s === D && (s = this._$AH[o]), a ||= !x(s) || s !== this._$AH[o], s === O ? e = O : e !== O && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === O ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, De = class extends N {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === O ? void 0 : e;
	}
}, Oe = class extends N {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== O);
	}
}, ke = class extends N {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = j(this, e, t, 0) ?? O) === D) return;
		let n = this._$AH, r = e === O && n !== O || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== O && (n === O || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Ae = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		j(this, e);
	}
}, je = {
	M: me,
	P: v,
	A: he,
	C: 1,
	L: Te,
	R: Ee,
	D: _e,
	V: j,
	I: M,
	H: N,
	N: Oe,
	U: ke,
	B: De,
	F: Ae
}, Me = g.litHtmlPolyfillSupport;
Me?.(A, M), (g.litHtmlVersions ??= []).push("3.3.3");
var Ne = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new M(t.insertBefore(b(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, Pe = globalThis, P = class extends h {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Ne(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return D;
	}
};
P._$litElement$ = !0, P.finalized = !0, Pe.litElementHydrateSupport?.({ LitElement: P });
var Fe = Pe.litElementPolyfillSupport;
Fe?.({ LitElement: P }), (Pe.litElementVersions ??= []).push("4.2.2");
// node_modules/@lit/reactive-element/decorators/custom-element.js
var F = (e) => (t, n) => {
	n === void 0 ? customElements.define(e, t) : n.addInitializer(() => {
		customElements.define(e, t);
	});
}, Ie = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	hasChanged: ue
}, Le = (e = Ie, t, n) => {
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
function I(e) {
	return (t, n) => typeof n == "object" ? Le(e, t, n) : ((e, t, n) => {
		let r = t.hasOwnProperty(n);
		return t.constructor.createProperty(n, e), r ? Object.getOwnPropertyDescriptor(t, n) : void 0;
	})(e, t, n);
}
// node_modules/@lit/reactive-element/decorators/state.js
function L(e) {
	return I({
		...e,
		state: !0,
		attribute: !1
	});
}
// src/api.ts
function Re(e, t) {
	return e.connection.subscribeMessage(t, { type: "at/subscribe" });
}
function ze(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/parse",
		text: t
	});
}
function Be(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/schedule",
		...t
	});
}
function Ve(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/cancel",
		job_ids: t
	});
}
function He(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/run_now",
		job_id: t
	});
}
function Ue(e, t, n) {
	return e.connection.sendMessagePromise({
		type: "at/reschedule",
		job_id: t,
		due: n
	});
}
function We(e) {
	return e.connection.sendMessagePromise({ type: "at/clear_history" });
}
function Ge(e) {
	return e.connection.sendMessagePromise({ type: "at/info" });
}
// src/add-job.ts
function Ke(e) {
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
function qe(e) {
	if (!e?.action) return;
	let t = { action: e.action }, n = Object.fromEntries(Object.entries(e.target ?? {}).filter(([, e]) => !(e == null || e === "" || Array.isArray(e) && e.length === 0)));
	return Object.keys(n).length > 0 && (t.target = n), e.data && Object.keys(e.data).length > 0 && (t.data = e.data), [t];
}
function Je(e, t) {
	return { delay_seconds: e === "+15m" ? 900 : 3600 };
}
function Ye(e) {
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
function Xe(e) {
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
function Ze(e, t) {
	return !Number.isNaN(e.getTime()) && e.getTime() > t.getTime();
}
// src/format.ts
var Qe = 36e5, $e = 864e5;
function et(e, t) {
	let n = e - t;
	if (n < 0 || n >= Qe) return "";
	let r = Math.floor(n / 1e3), i = Math.floor(r / 60), a = r % 60;
	return `${String(i).padStart(2, "0")}:${String(a).padStart(2, "0")}`;
}
function tt(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		timeZone: n,
		year: "numeric",
		month: "numeric",
		day: "numeric"
	}).format(e);
}
function R(e, t, n, r) {
	let i = new Intl.DateTimeFormat(n, {
		timeZone: r,
		hour: "numeric",
		minute: "2-digit"
	}).format(e);
	if (tt(e, n, r) === tt(t, n, r)) return i;
	let a = e.getTime() - t.getTime();
	return a > 0 && a < 7 * $e ? `${new Intl.DateTimeFormat(n, {
		timeZone: r,
		weekday: "short"
	}).format(e)} ${i}` : `${new Intl.DateTimeFormat(n, {
		timeZone: r,
		month: "short",
		day: "numeric"
	}).format(e)}, ${i}`;
}
function z(e, t) {
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
function nt(e, t) {
	let n = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(e);
	if (!n) return /* @__PURE__ */ new Date(NaN);
	let r = Date.UTC(+n[1], n[2] - 1, +n[3], +n[4], +n[5]);
	for (let e = 0; e < 1440; e++) {
		let n = r + e * 6e4, i = [z(n - 864e5, t), z(n + 864e5, t)].map((e) => n - e).sort((e, t) => e - t);
		for (let e of i) if (e + z(e, t) === n) return new Date(e);
	}
	return new Date(r - z(r, t));
}
function rt(e, t) {
	return new Date(e.getTime() + z(e.getTime(), t)).toISOString().slice(0, 16);
}
// src/ha-elements.ts
var it = [
	"hass-subpage",
	"ha-card",
	"ha-data-table",
	"ha-button",
	"ha-icon-button",
	"ha-dropdown",
	"ha-dropdown-item",
	"ha-svg-icon",
	"ha-filter-chip"
], B = ["ha-service-control", "ha-selector"];
async function at(e, t, n) {
	let r, i = new Promise((e) => r = setTimeout(e, n));
	return await Promise.race([Promise.all(t.map((t) => e.whenDefined(t).catch(() => void 0))), i]), clearTimeout(r), t.filter((t) => !e.get(t));
}
async function V(e, t) {
	await customElements.whenDefined(e);
	let n = document.createElement(e).routerOptions?.routes[t];
	typeof n == "object" && await n.load?.();
}
async function ot() {
	let e = document.createElement("partial-panel-resolver"), t = { config: {
		component_name: "config",
		url_path: "config"
	} };
	e.hass = { panels: t }, await e._getRoutes(t).routes.config.load();
}
async function st() {
	await ot(), await V("ha-panel-config", "automation");
}
async function ct() {
	await ot(), await V("ha-panel-config", "tools"), await V("ha-panel-tools", "action");
}
async function lt() {
	await st(), await V("ha-config-automation", "edit");
}
async function ut(e, t, n, r) {
	for (let i of n) {
		if (t.every((t) => e.get(t))) return;
		let n, a = new Promise((e) => n = setTimeout(e, r));
		await Promise.race([i().catch(() => void 0), a]), clearTimeout(n);
	}
}
async function dt(e, t, n, r) {
	let i = Date.now() + r;
	if (n.some((t) => !e.get(t))) {
		let e, n = new Promise((t) => e = setTimeout(t, r)), i = t().catch((e) => {
			console.warn("Scheduled Jobs: could not load Home Assistant's panel elements", e);
		});
		await Promise.race([i, n]), clearTimeout(e);
	}
	let a = await at(e, n, Math.max(0, i - Date.now()));
	return a.length && console.warn("Scheduled Jobs: Home Assistant elements missing:", a.join(", ")), a;
}
var ft;
function pt(e = 1e4) {
	return ft ??= dt(customElements, st, it, e), ft;
}
var mt;
function ht(e = 1e4) {
	let t = [ct, lt];
	return mt ??= dt(customElements, () => ut(customElements, B, t, e / t.length), B, e), mt;
}
function gt(e = customElements) {
	return B.every((t) => e.get(t));
}
// src/components/field-styles.ts
var H = u`
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
  .inline-error {
    color: var(--error-color, #db4437);
    font-size: 13px;
  }
`;
// \0@oxc-project+runtime@0.156.0/helpers/esm/decorate.js
function U(e, t, n, r) {
	var i = arguments.length, a = i < 3 ? t : r === null ? r = Object.getOwnPropertyDescriptor(t, n) : r, o;
	if (typeof Reflect == "object" && typeof Reflect.decorate == "function") a = Reflect.decorate(e, t, n, r);
	else for (var s = e.length - 1; s >= 0; s--) (o = e[s]) && (a = (i < 3 ? o(a) : i > 3 ? o(t, n, a) : o(t, n)) || a);
	return i > 3 && a && Object.defineProperty(t, n, a), a;
}
// src/components/pick-fallback.ts
var _t = [
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
], W = class extends P {
	constructor(...e) {
		super(...e), this.op = "turn_on", this.entity = "", this.varsText = "";
	}
	get domains() {
		return this.op === "script" ? ["script"] : this.op === "automation" ? ["automation"] : _t;
	}
	get entities() {
		let e = this.hass?.states ?? {};
		return Object.entries(e).filter(([e]) => this.domains.includes(e.split(".")[0])).map(([e, t]) => ({
			id: e,
			name: t.attributes.friendly_name || e
		})).sort((e, t) => e.name.localeCompare(t.name));
	}
	get vars() {
		return this.op === "script" ? Ye(this.varsText) : {
			ok: !0,
			value: {}
		};
	}
	get action() {
		let e = this.vars;
		if (this.entity !== "" && e.ok) return this.op === "script" ? Ke({
			script: this.entity,
			variables: e.value
		}) : this.op === "automation" ? Ke({ automation: this.entity }) : Ke({
			targetEntityIds: [this.entity],
			verb: this.op
		});
	}
	updated(e) {
		(e.has("op") || e.has("entity") || e.has("varsText")) && this.dispatchEvent(new CustomEvent("action-changed", { detail: { action: this.action } }));
	}
	render() {
		let e = this.vars;
		return E`
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
          ${this.entities.map((e) => E`<option value=${e.id} ?selected=${e.id === this.entity}>${e.name}</option>`)}
        </select>
      </div>
      ${this.op === "script" ? E`<div class="field">
            <label class="label" for="vars">Variables (JSON, optional)</label>
            <textarea id="vars" rows="3" placeholder='{"brightness": 80}' .value=${this.varsText} @input=${(e) => this.varsText = e.target.value}></textarea>
            ${e.ok ? O : E`<div class="inline-error">${e.error}</div>`}
          </div>` : O}
    `;
	}
	static {
		this.styles = [H, u`
      :host {
        display: block;
      }
    `];
	}
};
U([I({ attribute: !1 })], W.prototype, "hass", void 0), U([L()], W.prototype, "op", void 0), U([L()], W.prototype, "entity", void 0), U([L()], W.prototype, "varsText", void 0), W = U([F("at-pick-fallback")], W);
// src/components/pick-action.ts
var G = class extends P {
	constructor(...e) {
		super(...e), this.ready = !1;
	}
	emit(e) {
		this.dispatchEvent(new CustomEvent("action-changed", { detail: { action: e } }));
	}
	onValue(e) {
		e.stopPropagation(), this.value = e.detail.value, this.emit(qe(this.value));
	}
	onFallback(e) {
		this.emit(e.detail.action);
	}
	render() {
		return this.ready ? E`<ha-service-control .hass=${this.hass} .value=${this.value} narrow @value-changed=${this.onValue}></ha-service-control>` : E`<at-pick-fallback .hass=${this.hass} @action-changed=${this.onFallback}></at-pick-fallback>`;
	}
	static {
		this.styles = u`
    :host {
      display: block;
    }
    :host([hidden]) {
      display: none;
    }
  `;
	}
};
U([I({ attribute: !1 })], G.prototype, "hass", void 0), U([I({ type: Boolean })], G.prototype, "ready", void 0), U([L()], G.prototype, "value", void 0), G = U([F("at-pick-action")], G);
// src/components/sequence-editor.ts
var K = class extends P {
	constructor(...e) {
		super(...e), this.ready = !1, this.value = [], this.rawText = "";
	}
	emit(e) {
		this.dispatchEvent(new CustomEvent("action-changed", { detail: { action: e } }));
	}
	onValue(e) {
		e.stopPropagation();
		let t = e.detail.value;
		this.value = Array.isArray(t) ? t : [], this.emit(Array.isArray(t) && t.length > 0 ? t : void 0);
	}
	onRaw(e) {
		this.rawText = e;
		let t = Xe(e);
		this.emit(t.ok ? t.value : void 0);
	}
	fallback() {
		let e = this.rawText.trim() ? Xe(this.rawText) : void 0;
		return E`<div class="field">
      <label class="label" for="raw">Action list (JSON)</label>
      <textarea id="raw" rows="6" placeholder='[{"action": "light.turn_on", "target": {"entity_id": "light.porch"}}]' .value=${this.rawText} @input=${(e) => this.onRaw(e.target.value)}></textarea>
      ${e && !e.ok ? E`<div class="inline-error">${e.error}</div>` : O}
    </div>`;
	}
	render() {
		return this.ready ? E`<ha-selector .hass=${this.hass} .selector=${{ action: {} }} .value=${this.value} @value-changed=${this.onValue}></ha-selector>` : this.fallback();
	}
	static {
		this.styles = [H, u`
      :host {
        display: block;
      }
      :host([hidden]) {
        display: none;
      }
    `];
	}
};
U([I({ attribute: !1 })], K.prototype, "hass", void 0), U([I({ type: Boolean })], K.prototype, "ready", void 0), U([L()], K.prototype, "value", void 0), U([L()], K.prototype, "rawText", void 0), K = U([F("at-sequence-editor")], K);
// src/components/add-job-dialog.ts
var q = class extends P {
	constructor(...e) {
		super(...e), this.isAdmin = !1, this.open = !1, this.mode = "type", this.text = "", this.chip = "+15m", this.when = "", this.error = "", this.busy = !1, this.parseSeq = 0, this.openSeq = 0, this.onKey = (e) => {
			this.open && (e.key === "Escape" && !e.defaultPrevented && !this.inPopup(e) ? this.close() : e.key === "Tab" && !this.inOverlay(e) && this.trapFocus(e));
		};
	}
	inPopup(e) {
		let t = e.composedPath(), n = t.indexOf(this);
		return (n === -1 ? t : t.slice(0, n)).some((e) => e instanceof Element && (e.getAttribute("aria-expanded") === "true" || e.hasAttribute("open")));
	}
	inOverlay(e) {
		let t = e.composedPath(), n = t[0];
		return n instanceof Element && n !== document.body && !t.includes(this);
	}
	connectedCallback() {
		super.connectedCallback(), window.addEventListener("keydown", this.onKey);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), window.removeEventListener("keydown", this.onKey), window.clearTimeout(this.debounce);
	}
	updated(e) {
		e.has("open") && this.open && (this.returnFocus = vt(), this.reset(), this.decidePicker(), ((this.shadowRoot?.querySelector(".dialog"))?.querySelector("input, select, textarea") ?? this.focusables()[0])?.focus());
	}
	decidePicker() {
		let e = ++this.openSeq;
		ht().then(() => {
			e === this.openSeq && this.open && this.pickerReady === void 0 && (this.pickerReady = gt());
		});
	}
	focusables() {
		let e = this.shadowRoot?.querySelector(".dialog");
		return e ? [...e.querySelectorAll("button, input, select, textarea")].filter((e) => !e.disabled) : [];
	}
	trapFocus(e) {
		let t = this.focusables();
		if (!t.length) return;
		let n = this.shadowRoot?.activeElement, r = n !== null && !!this.shadowRoot?.querySelector(".dialog")?.contains(n), i = t[0], a = t[t.length - 1];
		e.shiftKey && (!r || n === i) ? (e.preventDefault(), a.focus()) : e.shiftKey || r && n !== a || (e.preventDefault(), i.focus());
	}
	reset() {
		window.clearTimeout(this.debounce), this.parseSeq++, this.mode = "type", this.text = "", this.preview = void 0, this.pickerReady = void 0, this.pickedAction = void 0, this.sequenceAction = void 0, this.chip = "+15m", this.when = "", this.error = "", this.busy = !1;
	}
	close() {
		this.busy || (this.reset(), this.open = !1, this.dispatchEvent(new CustomEvent("close-add-job")), this.returnFocus?.focus(), this.returnFocus = void 0);
	}
	onText(e) {
		this.text = e, this.preview = void 0, this.error = "", window.clearTimeout(this.debounce);
		let t = ++this.parseSeq;
		if (!e.trim() || !this.hass) return;
		let n = this.hass;
		this.debounce = window.setTimeout(() => {
			ze(n, e).then((e) => {
				if (t === this.parseSeq) {
					if (e.ok) {
						let t = R(new Date(e.due), /* @__PURE__ */ new Date(), this.locale, n.config.time_zone);
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
	get whenValid() {
		return this.chip !== "" || Ze(this.dueDate(), /* @__PURE__ */ new Date());
	}
	dueDate() {
		return nt(this.when, this.hass?.config.time_zone ?? "UTC");
	}
	get canSubmit() {
		return this.busy || !this.hass ? !1 : this.mode === "type" ? this.preview?.ok === !0 : this.mode === "sequence" ? this.sequenceAction !== void 0 && this.sequenceAction.length > 0 && this.whenValid : this.pickedAction !== void 0 && this.whenValid;
	}
	buildPayload() {
		if (this.mode === "type") return { text: this.text };
		let e = this.mode === "sequence" ? this.sequenceAction : this.pickedAction;
		return e ? this.chip ? {
			action: e,
			...Je(this.chip, /* @__PURE__ */ new Date())
		} : {
			action: e,
			due: this.dueDate().toISOString()
		} : "Choose an action";
	}
	async submit() {
		let e = this.hass;
		if (!e || !this.canSubmit) return;
		let t = this.buildPayload();
		if (typeof t == "string") this.error = t;
		else {
			this.busy = !0, this.error = "";
			try {
				await Be(e, t), this.busy = !1, this.close();
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
		let e = this.hass?.config.time_zone ?? "UTC", t = rt(/* @__PURE__ */ new Date(), e);
		return E`<div class="field">
      <span class="label">When</span>
      <div class="row">
        ${["+15m", "+1h"].map((e) => E`<button class="chip ${this.chip === e ? "on" : ""}" @click=${() => this.onChip(e)}>${e}</button>`)}
        <input type="datetime-local" aria-label="Date and time" .value=${this.when} min=${t} @input=${(e) => this.onWhen(e.target.value)} />
      </div>
      ${this.chip === "" && !this.whenValid ? E`<div class="inline-error">${this.when ? "Time must be in the future" : "Choose a time"}</div>` : O}
    </div>`;
	}
	pickSection() {
		let e = this.mode === "pick";
		return this.pickerReady === void 0 ? e ? E`<div class="field label" role="status">Loading…</div>` : O : E`<at-pick-action
      ?hidden=${!e}
      .hass=${this.hass}
      .ready=${this.pickerReady}
      @action-changed=${(e) => this.pickedAction = e.detail.action}
    ></at-pick-action>`;
	}
	typeSection() {
		return E`<div class="field">
      <label class="label" for="text">What should happen, and when?</label>
      <input id="text" type="text" placeholder="turn on the porch light at 11pm" .value=${this.text} @input=${(e) => this.onText(e.target.value)} />
      <div class=${this.preview ? this.preview.ok ? "preview ok" : "preview bad" : "preview"} aria-live="polite">
        ${this.preview ? this.preview.ok ? this.preview.text : this.preview.message : O}
      </div>
    </div>`;
	}
	sequenceSection() {
		let e = this.mode === "sequence";
		return this.pickerReady === void 0 ? e ? E`<div class="field label" role="status">Loading…</div>` : O : E`<at-sequence-editor
      ?hidden=${!e}
      .hass=${this.hass}
      .ready=${this.pickerReady}
      @action-changed=${(e) => this.sequenceAction = e.detail.action}
    ></at-sequence-editor>`;
	}
	tabBtn(e, t) {
		return E`<button class="mode ${this.mode === e ? "active" : ""}" role="tab" aria-selected=${this.mode === e} @click=${() => this.setMode(e)}>${t}</button>`;
	}
	render() {
		return this.open ? E`
      <div class="backdrop" @click=${() => this.close()}></div>
      <div class="dialog" role="dialog" aria-modal="true" aria-label="Add job">
        <h2>Add job</h2>
        <div class="modes" role="tablist">
          ${this.tabBtn("type", "Type it")} ${this.tabBtn("pick", "Pick it")} ${this.isAdmin ? this.tabBtn("sequence", "Sequence") : O}
        </div>
        ${this.mode === "type" ? this.typeSection() : O} ${this.pickSection()} ${this.isAdmin ? this.sequenceSection() : O}
        ${this.mode === "type" ? O : this.whenSection()}
        ${this.error ? E`<div class="error" role="alert">${this.error}</div>` : O}
        <div class="actions">
          <button ?disabled=${this.busy} @click=${() => this.close()}>Cancel</button>
          <button class="primary" ?disabled=${!this.canSubmit} @click=${() => void this.submit()}>Add</button>
        </div>
      </div>
    ` : O;
	}
	static {
		this.styles = [H, u`
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
        width: min(640px, calc(100vw - 32px));
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
      .preview {
        min-height: 20px;
        line-height: 20px;
      }
      .preview.ok {
        color: var(--success-color, #43a047);
      }
      .preview.bad {
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
    `];
	}
};
U([I({ attribute: !1 })], q.prototype, "hass", void 0), U([I({ type: Boolean })], q.prototype, "isAdmin", void 0), U([I({
	type: Boolean,
	reflect: !0
})], q.prototype, "open", void 0), U([L()], q.prototype, "mode", void 0), U([L()], q.prototype, "text", void 0), U([L()], q.prototype, "preview", void 0), U([L()], q.prototype, "pickerReady", void 0), U([L()], q.prototype, "pickedAction", void 0), U([L()], q.prototype, "sequenceAction", void 0), U([L()], q.prototype, "chip", void 0), U([L()], q.prototype, "when", void 0), U([L()], q.prototype, "error", void 0), U([L()], q.prototype, "busy", void 0), q = U([F("at-add-job-dialog")], q);
function vt() {
	let e = document.activeElement;
	for (; e?.shadowRoot?.activeElement;) e = e.shadowRoot.activeElement;
	return e instanceof HTMLElement ? e : void 0;
}
// node_modules/lit-html/directive.js
var J = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, yt = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), bt = class {
	constructor(e) {}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AT(e, t, n) {
		this._$Ct = e, this._$AM = t, this._$Ci = n;
	}
	_$AS(e, t) {
		return this.update(e, t);
	}
	update(e, t) {
		return this.render(...t);
	}
}, { I: xt } = je, St = (e) => e.strings === void 0, Ct = {}, wt = (e, t = Ct) => e._$AH = t, Tt = yt(class extends bt {
	constructor(e) {
		if (super(e), e.type !== J.PROPERTY && e.type !== J.ATTRIBUTE && e.type !== J.BOOLEAN_ATTRIBUTE) throw Error("The `live` directive is not allowed on child or event bindings");
		if (!St(e)) throw Error("`live` bindings can only contain a single expression");
	}
	render(e) {
		return e;
	}
	update(e, [t]) {
		if (t === D || t === O) return t;
		let n = e.element, r = e.name;
		if (e.type === J.PROPERTY) {
			if (t === n[r]) return D;
		} else if (e.type === J.BOOLEAN_ATTRIBUTE) {
			if (!!t === n.hasAttribute(r)) return D;
		} else if (e.type === J.ATTRIBUTE && n.getAttribute(r) === t + "") return D;
		return wt(e), t;
	}
}), Et = {
	voice: "Assist",
	llm: "Assist",
	panel: "Add job",
	reschedule: "Reschedule",
	todo: "To-do list"
}, Dt = {
	voice: "from Assist",
	llm: "from Assist",
	panel: "in the panel",
	todo: "from the to-do list",
	service: "by an action"
}, Ot = (e) => e === "voice" || e === "llm";
function kt(e, t) {
	if (!e) return;
	let n = Object.entries(t?.states ?? {}).find(([t, n]) => t.startsWith("person.") && n.attributes.user_id === e);
	return n ? n[1].attributes.friendly_name ?? n[0] : t?.user?.id === e ? t.user.name : void 0;
}
function At(e, t) {
	let n = e ? t?.devices?.[e] : void 0;
	return n?.name_by_user ?? n?.name ?? void 0;
}
function jt(e, t) {
	return t?.states?.[e]?.attributes.friendly_name ?? e;
}
var Mt = (e) => e.charAt(0).toUpperCase() + e.slice(1);
function Nt(e, t) {
	let { via: n, device_id: r, user_id: i, origin: a } = e.source, o = a ? [Mt(a.split(".")[0]), jt(a, t)] : [Et[n] ?? "Action"], s = Ot(n) ? At(r, t) : void 0;
	return [
		...o,
		s,
		kt(i, t)
	].filter(Boolean).join(" · ");
}
function Pt(e, t) {
	let n = e.cancelled_origin, r = Ot(e.cancelled_by) ? At(e.cancelled_device_id, t) : void 0, i = n ? `by ${n.split(".")[0]} ${jt(n, t)}` : [Dt[e.cancelled_by ?? ""], r].filter(Boolean).join(" · "), a = kt(e.cancelled_user_id, t);
	return [
		"Cancelled",
		i,
		a && `by ${a}`
	].filter(Boolean).join(" ");
}
function Ft(e, t) {
	switch (e.status) {
		case "failed": return e.result.error ?? "";
		case "missed": return "Home Assistant was off when it was due";
		case "cancelled": return Pt(e.result, t);
		default: return "";
	}
}
function It(e) {
	return typeof e == "string" && /^[\w./:-]+$/.test(e) ? e : JSON.stringify(e);
}
function Y(e, t = 0) {
	let n = "  ".repeat(t);
	if (Array.isArray(e)) return e.length === 0 ? `${n}[]` : e.map((e) => {
		if (typeof e == "object" && e) {
			let r = Y(e, t + 1).replace(/^\s+/, "");
			return `${n}- ${r}`;
		}
		return `${n}- ${It(e)}`;
	}).join("\n");
	if (typeof e == "object" && e) {
		let r = Object.entries(e);
		return r.length === 0 ? `${n}{}` : r.map(([e, r]) => typeof r == "object" && r && (Array.isArray(r) ? r.length : Object.keys(r).length) ? `${n}${e}:\n${Y(r, t + 1)}` : `${n}${e}: ${typeof r == "object" && r ? Y(r) : It(r)}`).join("\n");
	}
	return `${n}${It(e)}`;
}
// src/state.ts
var Lt = (e, t) => Date.parse(e.due) - Date.parse(t.due), Rt = (e) => Date.parse(e.finished_at ?? e.due), zt = (e, t) => Rt(t) - Rt(e);
function Bt(e) {
	return {
		pending: [...e.pending].sort(Lt),
		running: [...e.running].sort(Lt),
		history: [...e.history].sort(zt)
	};
}
function Vt(e, t) {
	let { job: n } = t, r = (e) => e.filter((e) => e.id !== n.id), i = {
		pending: r(e.pending),
		running: r(e.running),
		history: r(e.history)
	};
	return t.kind !== "removed" && (n.status === "pending" ? i.pending.push(n) : n.status === "running" ? i.running.push(n) : i.history.push(n)), Bt(i);
}
function Ht(e) {
	return `Upcoming (${e.pending.length})`;
}
function Ut(e, t, n, r = 15) {
	let i = t === "all" ? e : e.filter((e) => e.status === t);
	return {
		rows: n ? i : i.slice(0, r),
		matching: i.length
	};
}
// src/components/history-table.ts
var Wt = {
	done: n,
	failed: e,
	missed: r,
	cancelled: t
}, Gt = [
	{
		value: "all",
		label: "All"
	},
	{
		value: "done",
		label: "Done"
	},
	{
		value: "failed",
		label: "Failed"
	},
	{
		value: "missed",
		label: "Missed"
	},
	{
		value: "cancelled",
		label: "Cancelled"
	}
], X = class extends P {
	constructor(...e) {
		super(...e), this.history = [], this.now = Date.now(), this.narrow = !1, this.filter = "all", this.expanded = !1, this.editing = null, this.value = "";
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
		let t = nt(this.value, this.hass?.config.time_zone ?? "UTC");
		Number.isNaN(t.getTime()) || (this.fire("reschedule-job", {
			job: e,
			due: t.toISOString()
		}), this.editing = null, this.value = "");
	}
	selectFilter(e, t) {
		e.preventDefault(), this.filter = t;
	}
	startEditing(e) {
		this.editing = e.id, this.value = rt(new Date(Date.now() + 36e5), this.hass?.config.time_zone ?? "UTC");
	}
	actions(e) {
		let t = (e) => e.stopPropagation();
		return this.editing === e.id ? E`<div class="edit" @click=${t}>
      <input type="datetime-local" .value=${this.value} @input=${(e) => this.value = e.target.value} />
      <ha-button appearance="plain" size="s" @click=${() => this.submit(e.job)}>Save</ha-button>
      <ha-button appearance="plain" size="s" @click=${() => this.editing = null}>Cancel</ha-button>
    </div>` : E`<ha-button appearance="plain" size="s" @click=${(n) => (t(n), this.startEditing(e.job))}>Re-schedule</ha-button>`;
	}
	get columns() {
		return {
			status: {
				title: "",
				type: "icon",
				showNarrow: !0,
				template: (e) => E`<ha-svg-icon class="status ${e.job.status}" title=${e.job.status} .path=${Wt[e.job.status] ?? "M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z"}></ha-svg-icon>`
			},
			when: {
				title: "Time",
				minWidth: "120px"
			},
			summary: {
				title: "Job",
				main: !0,
				flex: 2
			},
			details: {
				title: "Details",
				flex: 2
			},
			actions: {
				title: "",
				showNarrow: !0,
				minWidth: this.editing ? "320px" : "130px",
				template: (e) => this.actions(e)
			}
		};
	}
	onRowClick(e) {
		let t = this.history.find((t) => t.id === e.detail.id);
		t && this.fire("open-job", { job: t });
	}
	render() {
		let { rows: e, matching: t } = Ut(this.history, this.filter, this.expanded), n = this.hass?.locale?.language ?? this.hass?.language ?? "en", r = this.hass?.config.time_zone ?? "UTC", i = e.map((e) => ({
			id: e.id,
			job: e,
			when: R(new Date(e.finished_at ?? e.due), new Date(this.now), n, r),
			summary: e.summary,
			details: Ft(e, this.hass)
		}));
		return E`<ha-card header="History">
      <div class="chips">
        ${Gt.map((e) => E`<ha-filter-chip .label=${e.label} .selected=${Tt(this.filter === e.value)} @click=${(t) => this.selectFilter(t, e.value)}></ha-filter-chip>`)}
      </div>
      <ha-data-table
        .columns=${this.columns}
        .data=${i}
        .narrow=${this.narrow}
        .noDataText=${this.history.length ? "No jobs match this filter." : "No history yet."}
        clickable
        auto-height
        @row-click=${this.onRowClick}
      ></ha-data-table>
      ${!this.expanded && t > 15 ? E`<div class="footer"><ha-button appearance="plain" @click=${() => this.expanded = !0}>Show all (${t})</ha-button></div>` : O}
    </ha-card>`;
	}
	static {
		this.styles = u`
    :host {
      display: block;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 0 16px 12px;
    }
    .footer {
      display: flex;
      justify-content: flex-end;
      padding: 8px;
    }
    .edit {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .status.done {
      color: var(--success-color);
    }
    .status.failed {
      color: var(--error-color);
    }
    .status.missed {
      color: var(--warning-color);
    }
    .status.cancelled {
      color: var(--secondary-text-color);
    }
  `;
	}
};
U([I({ attribute: !1 })], X.prototype, "hass", void 0), U([I({ attribute: !1 })], X.prototype, "history", void 0), U([I({ type: Number })], X.prototype, "now", void 0), U([I({ type: Boolean })], X.prototype, "narrow", void 0), U([L()], X.prototype, "filter", void 0), U([L()], X.prototype, "expanded", void 0), U([L()], X.prototype, "editing", void 0), U([L()], X.prototype, "value", void 0), X = U([F("at-history-table")], X);
// src/components/job-details.ts
var Z = class extends P {
	close() {
		this.dispatchEvent(new CustomEvent("close-details", {
			bubbles: !0,
			composed: !0
		}));
	}
	render() {
		let e = this.job;
		if (!e) return O;
		let t = this.hass?.config.time_zone ?? "UTC", n = this.hass?.locale?.language ?? this.hass?.language ?? "en", r = new Intl.DateTimeFormat(n, {
			timeZone: t,
			dateStyle: "medium",
			timeStyle: "medium"
		}).format(new Date(e.created_at)), i = e.intent ? `${e.intent.type}\n${Y(e.intent.slots)}` : Y(e.action ?? []);
		return E`<div class="backdrop" @click=${() => this.close()}>
      <div class="card" role="dialog" aria-label="Job details" @click=${(e) => e.stopPropagation()}>
        <h2>${e.summary}</h2>
        <dl>
          <dt>${e.intent ? "Intent" : "Action"}</dt>
          <dd><pre>${i}</pre></dd>
          <dt>Created by</dt>
          <dd>${Nt(e, this.hass)}</dd>
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
		this.styles = u`
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
U([I({ attribute: !1 })], Z.prototype, "hass", void 0), U([I({ attribute: !1 })], Z.prototype, "job", void 0), Z = U([F("at-job-details")], Z);
// src/components/upcoming-table.ts
var Q = class extends P {
	constructor(...e) {
		super(...e), this.pending = [], this.running = [], this.now = Date.now(), this.isAdmin = !1, this.narrow = !1;
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
		return et(t.getTime(), this.now) || R(t, new Date(this.now), this.hass?.locale?.language ?? this.hass?.language ?? "en", this.hass?.config.time_zone ?? "UTC");
	}
	actions(e) {
		return e.running ? O : E`${this.isAdmin || !e.job.raw_action ? E`<ha-icon-button .label=${"Run now"} .path=${"M8,5.14V19.14L19,12.14L8,5.14Z"} @click=${(t) => this.fire("run-job", e.job, t)}></ha-icon-button>` : O}
      <ha-icon-button .label=${"Cancel"} .path=${"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"} @click=${(t) => this.fire("cancel-job", e.job, t)}></ha-icon-button>`;
	}
	get columns() {
		return {
			when: {
				title: "When",
				main: !0,
				minWidth: "120px"
			},
			summary: {
				title: "Job",
				flex: 2
			},
			source: { title: "Source" },
			actions: {
				title: "",
				type: "icon-button",
				showNarrow: !0,
				minWidth: "96px",
				maxWidth: "96px",
				template: (e) => this.actions(e)
			}
		};
	}
	onRowClick(e) {
		let t = [...this.running, ...this.pending].find((t) => t.id === e.detail.id);
		t && this.fire("open-job", t);
	}
	render() {
		let e = (e, t) => ({
			id: e.id,
			job: e,
			running: t,
			when: t ? "Running…" : this.when(e),
			summary: e.summary,
			source: Nt(e, this.hass)
		}), t = [...this.running.map((t) => e(t, !0)), ...this.pending.map((t) => e(t, !1))];
		return E`<ha-card .header=${Ht({
			pending: this.pending,
			running: this.running,
			history: []
		})}>
      <ha-data-table
        .columns=${this.columns}
        .data=${t}
        .narrow=${this.narrow}
        .noDataText=${"Nothing scheduled."}
        clickable
        auto-height
        @row-click=${this.onRowClick}
      ></ha-data-table>
    </ha-card>`;
	}
	static {
		this.styles = u`
    :host {
      display: block;
    }
  `;
	}
};
U([I({ attribute: !1 })], Q.prototype, "hass", void 0), U([I({ attribute: !1 })], Q.prototype, "pending", void 0), U([I({ attribute: !1 })], Q.prototype, "running", void 0), U([I({ type: Number })], Q.prototype, "now", void 0), U([I({ type: Boolean })], Q.prototype, "isAdmin", void 0), U([I({ type: Boolean })], Q.prototype, "narrow", void 0), Q = U([F("at-upcoming-table")], Q);
// src/localize.ts
var Kt = "component.at.config_panel.";
function qt(e) {
	return (t, n) => e.localize(`${Kt}${t}`, n) || t;
}
// src/reconnect.ts
var Jt = 1e3, Yt = 3e4;
function Xt(e) {
	return Math.min(Jt * 2 ** Math.min(e, 10), Yt);
}
// src/at-panel.ts
var $ = class extends P {
	constructor(...e) {
		super(...e), this.narrow = !1, this.data = {
			pending: [],
			running: [],
			history: []
		}, this.now = Date.now(), this.reconnecting = !0, this.error = "", this.confirmCancelAll = !1, this.addOpen = !1, this.attempt = 0, this.subscribed = !1, this.gone = !1, this.generation = 0, this.onRun = (e) => {
			let t = this.hass;
			t && this.call(() => He(t, e.detail.job.id));
		}, this.onCancel = (e) => {
			let t = this.hass;
			t && this.call(() => Ve(t, [e.detail.job.id]));
		}, this.onReschedule = (e) => {
			let t = this.hass;
			t && this.call(() => Ue(t, e.detail.job.id, e.detail.due));
		}, this.onOpen = (e) => this.details = e.detail.job;
	}
	connectedCallback() {
		super.connectedCallback(), this.gone = !1, this.generation++, window.clearInterval(this.tick), this.tick = window.setInterval(() => this.now = Date.now(), 1e3), this.hass && this.start();
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this.gone = !0, this.generation++, window.clearInterval(this.tick), window.clearTimeout(this.retryTimer), this.subscribed = !1, this.unsub?.().catch(() => void 0), this.unsub = void 0;
	}
	updated(e) {
		e.has("hass") && this.hass && this.hass.language !== this.translationsLanguage && this.loadTranslations(this.hass), e.has("hass") && this.hass && !this.subscribed && !this.gone && this.start();
	}
	async loadTranslations(e) {
		this.translationsLanguage = e.language;
		try {
			await e.loadBackendTranslation("config_panel", "at");
		} catch {
			return;
		}
		this.requestUpdate();
	}
	get localize() {
		return this.hass ? qt(this.hass) : (e) => e;
	}
	async start() {
		this.hass && !this.subscribed && (this.subscribed = !0, Ge(this.hass).then((e) => this.atInfo = e, () => void 0), pt().then((e) => this.missing = e), await this.subscribe());
	}
	async subscribe() {
		if (!this.hass || this.gone) return;
		let e = this.generation;
		try {
			let t = await Re(this.hass, (t) => {
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
		if ("snapshot" in e) this.data = Bt(e.snapshot), this.reconnecting = !1, this.attempt = 0;
		else if ("change" in e) this.data = Vt(this.data, e.change);
		else if ("stopped" in e) {
			let e = this.unsub;
			this.unsub = void 0, e?.().catch(() => void 0), this.scheduleRetry();
		}
	}
	scheduleRetry() {
		if (this.reconnecting = !0, this.gone) return;
		let e = Xt(this.attempt++);
		window.clearTimeout(this.retryTimer), this.retryTimer = window.setTimeout(() => void this.subscribe(), e);
	}
	async call(e) {
		try {
			await e();
		} catch (e) {
			let t = e?.message;
			this.error = t || this.localize("panel.request_failed");
		}
	}
	cancelAll() {
		let e = this.hass;
		if (!e) return;
		if (!this.confirmCancelAll) {
			this.confirmCancelAll = !0;
			return;
		}
		this.confirmCancelAll = !1;
		let t = this.data.pending.map((e) => e.id);
		t.length && this.call(() => Ve(e, t));
	}
	clearHistory() {
		let e = this.hass;
		this.confirmCancelAll = !1, e && this.call(() => We(e));
	}
	onMenuSelect(e) {
		let t = e.detail.item.value;
		t === "cancel-all" ? (this.confirmCancelAll || e.preventDefault(), this.cancelAll()) : t === "clear-history" && this.clearHistory();
	}
	get title_() {
		let e = this.panel?.config?.title;
		return typeof e == "string" && e ? e : this.localize("panel.title");
	}
	render() {
		if (this.missing === void 0) return O;
		if (this.missing.length) return E`<div class="missing">
        <p>${this.localize("panel.update_needed")}</p>
        <p>${this.localize("panel.missing_elements", { elements: this.missing.join(", ") })}</p>
      </div>`;
		let e = this.localize, t = this.atInfo?.is_admin ?? !1;
		return E`
      <hass-subpage main-page .hass=${this.hass} .narrow=${this.narrow} .header=${this.title_}>
        <ha-dropdown
          slot="toolbar-icon"
          placement="bottom-end"
          @wa-select=${this.onMenuSelect}
          @wa-after-hide=${() => this.confirmCancelAll = !1}
        >
          <ha-icon-button slot="trigger" .label=${e("panel.more_options")} .path=${"M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z"}></ha-icon-button>
          <ha-dropdown-item value="cancel-all">${e(this.confirmCancelAll ? "panel.confirm_cancel_all" : "panel.cancel_all")}</ha-dropdown-item>
          <ha-dropdown-item value="clear-history">${e("panel.clear_history")}</ha-dropdown-item>
        </ha-dropdown>
        <div class="content" @run-job=${this.onRun} @cancel-job=${this.onCancel} @reschedule-job=${this.onReschedule} @open-job=${this.onOpen}>
          ${this.reconnecting ? E`<div class="notice">${e("panel.reconnecting")}</div>` : O}
          ${this.error ? E`<div class="error" role="alert">${this.error}<button aria-label=${e("panel.dismiss")} @click=${() => this.error = ""}>✕</button></div>` : O}
          <at-upcoming-table
            .hass=${this.hass} .localize=${e}
            .pending=${this.data.pending}
            .running=${this.data.running}
            .now=${this.now}
            .isAdmin=${t}
            .narrow=${this.narrow}
          ></at-upcoming-table>
          <at-history-table .hass=${this.hass} .localize=${e} .history=${this.data.history} .now=${this.now} .narrow=${this.narrow}></at-history-table>
        </div>
        <ha-button slot="fab" size="l" @click=${() => this.addOpen = !0}>
          <ha-svg-icon slot="start" .path=${"M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"}></ha-svg-icon>
          ${e("panel.add_job")}
        </ha-button>
      </hass-subpage>
      <at-add-job-dialog .hass=${this.hass} .localize=${e} .isAdmin=${t} .open=${this.addOpen} @close-add-job=${() => this.addOpen = !1}></at-add-job-dialog>
      <at-job-details .hass=${this.hass} .localize=${e} .job=${this.details} @close-details=${() => this.details = void 0}></at-job-details>
    `;
	}
	static {
		this.styles = u`
    :host {
      display: block;
      height: 100vh;
      height: 100dvh;
    }
    .content {
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      gap: 16px;
      max-width: 1000px;
      margin: 0 auto;
      padding: 16px 16px 88px;
    }
    .notice {
      color: var(--secondary-text-color);
    }
    .error {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      border-radius: 4px;
      color: var(--text-primary-color);
      background: var(--error-color);
    }
    .error button {
      font: inherit;
      color: inherit;
      background: none;
      border: none;
      cursor: pointer;
    }
    .missing {
      padding: 32px 16px;
      color: var(--primary-text-color);
    }
  `;
	}
};
U([I({ attribute: !1 })], $.prototype, "hass", void 0), U([I({ type: Boolean })], $.prototype, "narrow", void 0), U([I({ attribute: !1 })], $.prototype, "panel", void 0), U([I({ attribute: !1 })], $.prototype, "route", void 0), U([L()], $.prototype, "missing", void 0), U([L()], $.prototype, "data", void 0), U([L()], $.prototype, "now", void 0), U([L()], $.prototype, "reconnecting", void 0), U([L()], $.prototype, "error", void 0), U([L()], $.prototype, "confirmCancelAll", void 0), U([L()], $.prototype, "details", void 0), U([L()], $.prototype, "atInfo", void 0), U([L()], $.prototype, "addOpen", void 0), $ = U([F("at-panel")], $);
export { $ as AtPanel };
