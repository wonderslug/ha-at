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
}, h = (e, t) => !te(e, t), ue = {
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
	static createProperty(e, t = ue) {
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
		return this.elementProperties.get(e) ?? ue;
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
g.elementStyles = [], g.shadowRootOptions = { mode: "open" }, g[p("elementProperties")] = /* @__PURE__ */ new Map(), g[p("finalized")] = /* @__PURE__ */ new Map(), le?.({ ReactiveElement: g }), (f.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var _ = globalThis, de = (e) => e, v = _.trustedTypes, fe = v ? v.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, pe = "$lit$", y = `lit$${Math.random().toFixed(9).slice(2)}$`, b = "?" + y, me = `<${b}>`, x = document, S = () => x.createComment(""), C = (e) => e === null || typeof e != "object" && typeof e != "function", w = Array.isArray, he = (e) => w(e) || typeof e?.[Symbol.iterator] == "function", T = "[ 	\n\f\r]", E = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ge = /-->/g, _e = />/g, D = RegExp(`>|${T}(?:([^\\s"'>=/]+)(${T}*=${T}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), ve = /'/g, ye = /"/g, be = /^(?:script|style|textarea|title)$/i, O = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), k = Symbol.for("lit-noChange"), A = Symbol.for("lit-nothing"), xe = /* @__PURE__ */ new WeakMap(), j = x.createTreeWalker(x, 129);
function Se(e, t) {
	if (!w(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return fe === void 0 ? t : fe.createHTML(t);
}
var Ce = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = E;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === E ? c[1] === "!--" ? o = ge : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = D) : (be.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = D) : o = _e : o === D ? c[0] === ">" ? (o = i ?? E, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? D : c[3] === "\"" ? ye : ve) : o === ye || o === ve ? o = D : o === ge || o === _e ? o = E : (o = D, i = void 0);
		let d = o === D && e[t + 1].startsWith("/>") ? " " : "";
		a += o === E ? n + me : l >= 0 ? (r.push(s), n.slice(0, l) + pe + n.slice(l) + y + d) : n + y + (l === -2 ? t : d);
	}
	return [Se(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, M = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = Ce(t, n);
		if (this.el = e.createElement(l, r), j.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = j.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(pe)) {
					let t = u[o++], n = i.getAttribute(e).split(y), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? Te : r[1] === "?" ? Ee : r[1] === "@" ? De : F
					}), i.removeAttribute(e);
				} else e.startsWith(y) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (be.test(i.tagName)) {
					let e = i.textContent.split(y), t = e.length - 1;
					if (t > 0) {
						i.textContent = v ? v.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], S()), j.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], S());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === b) c.push({
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
		let n = x.createElement("template");
		return n.innerHTML = e, n;
	}
};
function N(e, t, n = e, r) {
	if (t === k) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = C(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = N(e, i._$AS(e, t.values), i, r)), t;
}
var we = class {
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
		j.currentNode = r;
		let i = j.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new P(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Oe(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = j.nextNode(), a++);
		}
		return j.currentNode = x, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, P = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = N(this, e, t), C(e) ? e === A || e == null || e === "" ? (this._$AH !== A && this._$AR(), this._$AH = A) : e !== this._$AH && e !== k && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? he(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== A && C(this._$AH) ? this._$AA.nextSibling.data = e : this.T(x.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = M.createElement(Se(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new we(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = xe.get(e.strings);
		return t === void 0 && xe.set(e.strings, t = new M(e)), t;
	}
	k(t) {
		w(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(S()), this.O(S()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = de(e).nextSibling;
			de(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, F = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = A, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = A;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = N(this, e, t, 0), a = !C(e) || e !== this._$AH && e !== k, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = N(this, r[n + o], t, o), s === k && (s = this._$AH[o]), a ||= !C(s) || s !== this._$AH[o], s === A ? e = A : e !== A && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, Te = class extends F {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === A ? void 0 : e;
	}
}, Ee = class extends F {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== A);
	}
}, De = class extends F {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = N(this, e, t, 0) ?? A) === k) return;
		let n = this._$AH, r = e === A && n !== A || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== A && (n === A || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Oe = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		N(this, e);
	}
}, ke = {
	M: pe,
	P: y,
	A: b,
	C: 1,
	L: Ce,
	R: we,
	D: he,
	V: N,
	I: P,
	H: F,
	N: Ee,
	U: De,
	B: Te,
	F: Oe
}, Ae = _.litHtmlPolyfillSupport;
Ae?.(M, P), (_.litHtmlVersions ??= []).push("3.3.3");
var je = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new P(t.insertBefore(S(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, I = globalThis, L = class extends g {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = je(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return k;
	}
};
L._$litElement$ = !0, L.finalized = !0, I.litElementHydrateSupport?.({ LitElement: L });
var Me = I.litElementPolyfillSupport;
Me?.({ LitElement: L }), (I.litElementVersions ??= []).push("4.2.2");
// node_modules/@lit/reactive-element/decorators/custom-element.js
var R = (e) => (t, n) => {
	n === void 0 ? customElements.define(e, t) : n.addInitializer(() => {
		customElements.define(e, t);
	});
}, Ne = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	hasChanged: h
}, Pe = (e = Ne, t, n) => {
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
function z(e) {
	return (t, n) => typeof n == "object" ? Pe(e, t, n) : ((e, t, n) => {
		let r = t.hasOwnProperty(n);
		return t.constructor.createProperty(n, e), r ? Object.getOwnPropertyDescriptor(t, n) : void 0;
	})(e, t, n);
}
// node_modules/@lit/reactive-element/decorators/state.js
function B(e) {
	return z({
		...e,
		state: !0,
		attribute: !1
	});
}
// src/api.ts
function Fe(e, t) {
	return e.connection.subscribeMessage(t, { type: "at/subscribe" });
}
function Ie(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/parse",
		text: t
	});
}
function Le(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/schedule",
		...t
	});
}
function Re(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/cancel",
		job_ids: t
	});
}
function ze(e, t) {
	return e.connection.sendMessagePromise({
		type: "at/run_now",
		job_id: t
	});
}
function Be(e, t, n) {
	return e.connection.sendMessagePromise({
		type: "at/reschedule",
		job_id: t,
		due: n
	});
}
function Ve(e) {
	return e.connection.sendMessagePromise({ type: "at/clear_history" });
}
function He(e) {
	return e.connection.sendMessagePromise({ type: "at/info" });
}
// src/add-job.ts
function V(e) {
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
function Ue(e, t) {
	return { delay_seconds: e === "+15m" ? 900 : 3600 };
}
function We(e) {
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
function H(e) {
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
function Ge(e, t) {
	return !Number.isNaN(e.getTime()) && e.getTime() > t.getTime();
}
// src/format.ts
var Ke = 36e5, qe = 864e5;
function Je(e, t) {
	let n = e - t;
	if (n < 0 || n >= Ke) return "";
	let r = Math.floor(n / 1e3), i = Math.floor(r / 60), a = r % 60;
	return `${String(i).padStart(2, "0")}:${String(a).padStart(2, "0")}`;
}
function Ye(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		timeZone: n,
		year: "numeric",
		month: "numeric",
		day: "numeric"
	}).format(e);
}
function U(e, t, n, r) {
	let i = new Intl.DateTimeFormat(n, {
		timeZone: r,
		hour: "numeric",
		minute: "2-digit"
	}).format(e);
	if (Ye(e, n, r) === Ye(t, n, r)) return i;
	let a = e.getTime() - t.getTime();
	return a > 0 && a < 7 * qe ? `${new Intl.DateTimeFormat(n, {
		timeZone: r,
		weekday: "short"
	}).format(e)} ${i}` : `${new Intl.DateTimeFormat(n, {
		timeZone: r,
		month: "short",
		day: "numeric"
	}).format(e)}, ${i}`;
}
function W(e, t) {
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
function Xe(e, t) {
	let n = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(e);
	if (!n) return /* @__PURE__ */ new Date(NaN);
	let r = Date.UTC(+n[1], n[2] - 1, +n[3], +n[4], +n[5]);
	for (let e = 0; e < 1440; e++) {
		let n = r + e * 6e4, i = [W(n - 864e5, t), W(n + 864e5, t)].map((e) => n - e).sort((e, t) => e - t);
		for (let e of i) if (e + W(e, t) === n) return new Date(e);
	}
	return new Date(r - W(r, t));
}
function Ze(e, t) {
	return new Date(e.getTime() + W(e.getTime(), t)).toISOString().slice(0, 16);
}
// \0@oxc-project+runtime@0.156.0/helpers/esm/decorate.js
function G(e, t, n, r) {
	var i = arguments.length, a = i < 3 ? t : r === null ? r = Object.getOwnPropertyDescriptor(t, n) : r, o;
	if (typeof Reflect == "object" && typeof Reflect.decorate == "function") a = Reflect.decorate(e, t, n, r);
	else for (var s = e.length - 1; s >= 0; s--) (o = e[s]) && (a = (i < 3 ? o(a) : i > 3 ? o(t, n, a) : o(t, n)) || a);
	return i > 3 && a && Object.defineProperty(t, n, a), a;
}
// src/components/add-job-dialog.ts
var Qe = [
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
], K = class extends L {
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
			Ie(n, e).then((e) => {
				if (t === this.parseSeq) {
					if (e.ok) {
						let t = U(new Date(e.due), /* @__PURE__ */ new Date(), this.locale, n.config.time_zone);
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
		return this.op === "script" ? ["script"] : this.op === "automation" ? ["automation"] : Qe;
	}
	get entities() {
		let e = this.hass?.states ?? {};
		return Object.entries(e).filter(([e]) => this.domains.includes(e.split(".")[0])).map(([e, t]) => ({
			id: e,
			name: t.attributes.friendly_name || e
		})).sort((e, t) => e.name.localeCompare(t.name));
	}
	get vars() {
		return this.op === "script" ? We(this.varsText) : {
			ok: !0,
			value: {}
		};
	}
	get whenValid() {
		return this.chip !== "" || Ge(this.dueDate(), /* @__PURE__ */ new Date());
	}
	dueDate() {
		return Xe(this.when, this.hass?.config.time_zone ?? "UTC");
	}
	get canSubmit() {
		return this.busy || !this.hass ? !1 : this.mode === "type" ? this.preview?.ok === !0 : this.mode === "raw" ? this.rawText.trim() !== "" && this.whenValid : this.entity !== "" && this.vars.ok && this.whenValid;
	}
	buildPayload() {
		if (this.mode === "type") return { text: this.text };
		let e = this.mode === "raw", t;
		if (e) {
			let e = H(this.rawText);
			if (!e.ok) return e.error;
			t = e.value;
		} else if (this.op === "script") {
			let e = We(this.varsText);
			if (!e.ok) return e.error;
			t = V({
				script: this.entity,
				variables: e.value
			});
		} else t = this.op === "automation" ? V({ automation: this.entity }) : V({
			targetEntityIds: [this.entity],
			verb: this.op
		});
		return this.chip ? {
			action: t,
			...Ue(this.chip, /* @__PURE__ */ new Date())
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
				await Le(e, t), this.close();
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
		let e = this.hass?.config.time_zone ?? "UTC", t = Ze(/* @__PURE__ */ new Date(), e);
		return O`<div class="field">
      <span class="label">When</span>
      <div class="row">
        ${["+15m", "+1h"].map((e) => O`<button class="chip ${this.chip === e ? "on" : ""}" @click=${() => this.onChip(e)}>${e}</button>`)}
        <input type="datetime-local" aria-label="Date and time" .value=${this.when} min=${t} @input=${(e) => this.onWhen(e.target.value)} />
      </div>
      ${this.chip === "" && !this.whenValid ? O`<div class="inline-error">${this.when ? "Time must be in the future" : "Choose a time"}</div>` : A}
    </div>`;
	}
	pickSection() {
		let e = this.op === "script", t = this.vars;
		return O`
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
          ${this.entities.map((e) => O`<option value=${e.id} ?selected=${e.id === this.entity}>${e.name}</option>`)}
        </select>
      </div>
      ${e ? O`<div class="field">
            <label class="label" for="vars">Variables (JSON, optional)</label>
            <textarea id="vars" rows="3" placeholder='{"brightness": 80}' .value=${this.varsText} @input=${(e) => this.varsText = e.target.value}></textarea>
            ${t.ok ? A : O`<div class="inline-error">${t.error}</div>`}
          </div>` : A}
      ${this.whenSection()}
    `;
	}
	typeSection() {
		return O`<div class="field">
      <label class="label" for="text">What should happen, and when?</label>
      <input id="text" type="text" placeholder="turn on the porch light at 11pm" .value=${this.text} @input=${(e) => this.onText(e.target.value)} />
      ${this.preview ? O`<div class=${this.preview.ok ? "preview ok" : "preview bad"}>${this.preview.ok ? this.preview.text : this.preview.message}</div>` : A}
    </div>`;
	}
	rawSection() {
		let e = this.rawText.trim() ? H(this.rawText) : void 0;
		return O`<div class="field">
        <label class="label" for="raw">Action list (JSON)</label>
        <textarea id="raw" rows="6" placeholder='[{"action": "light.turn_on", "target": {"entity_id": "light.porch"}}]' .value=${this.rawText} @input=${(e) => this.rawText = e.target.value}></textarea>
        ${e && !e.ok ? O`<div class="inline-error">${e.error}</div>` : A}
      </div>
      ${this.whenSection()}`;
	}
	tabBtn(e, t) {
		return O`<button class="mode ${this.mode === e ? "active" : ""}" role="tab" aria-selected=${this.mode === e} @click=${() => this.setMode(e)}>${t}</button>`;
	}
	render() {
		if (!this.open) return A;
		let e = this.mode === "raw" && this.rawText.trim() !== "" && !H(this.rawText).ok;
		return O`
      <div class="backdrop" @click=${() => this.close()}></div>
      <div class="dialog" role="dialog" aria-modal="true" aria-label="Add job">
        <h2>Add job</h2>
        <div class="modes" role="tablist">
          ${this.tabBtn("type", "Type it")} ${this.tabBtn("pick", "Pick it")} ${this.isAdmin ? this.tabBtn("raw", "Raw") : A}
        </div>
        ${this.mode === "type" ? this.typeSection() : this.mode === "pick" ? this.pickSection() : this.rawSection()}
        ${this.error ? O`<div class="error" role="alert">${this.error}</div>` : A}
        <div class="actions">
          <button @click=${() => this.close()}>Cancel</button>
          <button class="primary" ?disabled=${!this.canSubmit || e} @click=${() => void this.submit()}>Add</button>
        </div>
      </div>
    `;
	}
	static {
		this.styles = u`
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
G([z({ attribute: !1 })], K.prototype, "hass", void 0), G([z({ type: Boolean })], K.prototype, "isAdmin", void 0), G([z({
	type: Boolean,
	reflect: !0
})], K.prototype, "open", void 0), G([B()], K.prototype, "mode", void 0), G([B()], K.prototype, "text", void 0), G([B()], K.prototype, "preview", void 0), G([B()], K.prototype, "op", void 0), G([B()], K.prototype, "entity", void 0), G([B()], K.prototype, "varsText", void 0), G([B()], K.prototype, "chip", void 0), G([B()], K.prototype, "when", void 0), G([B()], K.prototype, "rawText", void 0), G([B()], K.prototype, "error", void 0), G([B()], K.prototype, "busy", void 0), K = G([R("at-add-job-dialog")], K);
// node_modules/lit-html/directive.js
var q = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, $e = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), et = class {
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
}, { I: tt } = ke, nt = (e) => e.strings === void 0, rt = {}, it = (e, t = rt) => e._$AH = t, at = $e(class extends et {
	constructor(e) {
		if (super(e), e.type !== q.PROPERTY && e.type !== q.ATTRIBUTE && e.type !== q.BOOLEAN_ATTRIBUTE) throw Error("The `live` directive is not allowed on child or event bindings");
		if (!nt(e)) throw Error("`live` bindings can only contain a single expression");
	}
	render(e) {
		return e;
	}
	update(e, [t]) {
		if (t === k || t === A) return t;
		let n = e.element, r = e.name;
		if (e.type === q.PROPERTY) {
			if (t === n[r]) return k;
		} else if (e.type === q.BOOLEAN_ATTRIBUTE) {
			if (!!t === n.hasAttribute(r)) return k;
		} else if (e.type === q.ATTRIBUTE && n.getAttribute(r) === t + "") return k;
		return it(e), t;
	}
}), ot = (e, t) => Date.parse(e.due) - Date.parse(t.due), st = (e) => Date.parse(e.finished_at ?? e.due), ct = (e, t) => st(t) - st(e);
function lt(e) {
	return {
		pending: [...e.pending].sort(ot),
		running: [...e.running].sort(ot),
		history: [...e.history].sort(ct)
	};
}
function ut(e, t) {
	let { job: n } = t, r = (e) => e.filter((e) => e.id !== n.id), i = {
		pending: r(e.pending),
		running: r(e.running),
		history: r(e.history)
	};
	return t.kind !== "removed" && (n.status === "pending" ? i.pending.push(n) : n.status === "running" ? i.running.push(n) : i.history.push(n)), lt(i);
}
function dt(e) {
	return `Upcoming (${e.pending.length})`;
}
function ft(e, t, n, r = 15) {
	let i = t === "all" ? e : e.filter((e) => e.status === t);
	return {
		rows: n ? i : i.slice(0, r),
		matching: i.length
	};
}
// src/components/history-table.ts
var pt = {
	done: n,
	failed: e,
	missed: r,
	cancelled: t
}, mt = [
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
], J = class extends L {
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
		let t = Xe(this.value, this.hass?.config.time_zone ?? "UTC");
		Number.isNaN(t.getTime()) || (this.fire("reschedule-job", {
			job: e,
			due: t.toISOString()
		}), this.editing = null, this.value = "");
	}
	selectFilter(e, t) {
		e.preventDefault(), this.filter = t;
	}
	startEditing(e) {
		this.editing = e.id, this.value = Ze(new Date(Date.now() + 36e5), this.hass?.config.time_zone ?? "UTC");
	}
	actions(e) {
		let t = (e) => e.stopPropagation();
		return this.editing === e.id ? O`<div class="edit" @click=${t}>
      <input type="datetime-local" .value=${this.value} @input=${(e) => this.value = e.target.value} />
      <ha-button appearance="plain" size="s" @click=${() => this.submit(e.job)}>Save</ha-button>
      <ha-button appearance="plain" size="s" @click=${() => this.editing = null}>Cancel</ha-button>
    </div>` : O`<ha-button appearance="plain" size="s" @click=${(n) => (t(n), this.startEditing(e.job))}>Re-schedule</ha-button>`;
	}
	get columns() {
		return {
			status: {
				title: "",
				type: "icon",
				showNarrow: !0,
				template: (e) => O`<ha-svg-icon class="status ${e.job.status}" title=${e.job.status} .path=${pt[e.job.status] ?? "M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z"}></ha-svg-icon>`
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
			result: { title: "Result" },
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
		let { rows: e, matching: t } = ft(this.history, this.filter, this.expanded), n = this.hass?.locale?.language ?? this.hass?.language ?? "en", r = this.hass?.config.time_zone ?? "UTC", i = e.map((e) => ({
			id: e.id,
			job: e,
			when: U(new Date(e.finished_at ?? e.due), new Date(this.now), n, r),
			summary: e.summary,
			result: e.result.error ?? ""
		}));
		return O`<ha-card header="History">
      <div class="chips">
        ${mt.map((e) => O`<ha-filter-chip .label=${e.label} .selected=${at(this.filter === e.value)} @click=${(t) => this.selectFilter(t, e.value)}></ha-filter-chip>`)}
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
      ${!this.expanded && t > 15 ? O`<div class="footer"><ha-button appearance="plain" @click=${() => this.expanded = !0}>Show all (${t})</ha-button></div>` : A}
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
G([z({ attribute: !1 })], J.prototype, "hass", void 0), G([z({ attribute: !1 })], J.prototype, "history", void 0), G([z({ type: Number })], J.prototype, "now", void 0), G([z({ type: Boolean })], J.prototype, "narrow", void 0), G([B()], J.prototype, "filter", void 0), G([B()], J.prototype, "expanded", void 0), G([B()], J.prototype, "editing", void 0), G([B()], J.prototype, "value", void 0), J = G([R("at-history-table")], J);
// src/source.ts
function ht(e, t) {
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
var Z = class extends L {
	close() {
		this.dispatchEvent(new CustomEvent("close-details", {
			bubbles: !0,
			composed: !0
		}));
	}
	render() {
		let e = this.job;
		if (!e) return A;
		let t = this.hass?.config.time_zone ?? "UTC", n = this.hass?.locale?.language ?? this.hass?.language ?? "en", r = new Intl.DateTimeFormat(n, {
			timeZone: t,
			dateStyle: "medium",
			timeStyle: "medium"
		}).format(new Date(e.created_at)), i = e.intent ? `${e.intent.type}\n${X(e.intent.slots)}` : X(e.action ?? []);
		return O`<div class="backdrop" @click=${() => this.close()}>
      <div class="card" role="dialog" aria-label="Job details" @click=${(e) => e.stopPropagation()}>
        <h2>${e.summary}</h2>
        <dl>
          <dt>${e.intent ? "Intent" : "Action"}</dt>
          <dd><pre>${i}</pre></dd>
          <dt>Created by</dt>
          <dd>${ht(e, this.hass)}</dd>
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
G([z({ attribute: !1 })], Z.prototype, "hass", void 0), G([z({ attribute: !1 })], Z.prototype, "job", void 0), Z = G([R("at-job-details")], Z);
// src/components/upcoming-table.ts
var Q = class extends L {
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
		return Je(t.getTime(), this.now) || U(t, new Date(this.now), this.hass?.locale?.language ?? this.hass?.language ?? "en", this.hass?.config.time_zone ?? "UTC");
	}
	actions(e) {
		return e.running ? A : O`${this.isAdmin || !e.job.raw_action ? O`<ha-icon-button .label=${"Run now"} .path=${"M8,5.14V19.14L19,12.14L8,5.14Z"} @click=${(t) => this.fire("run-job", e.job, t)}></ha-icon-button>` : A}
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
			source: ht(e, this.hass)
		}), t = [...this.running.map((t) => e(t, !0)), ...this.pending.map((t) => e(t, !1))];
		return O`<ha-card .header=${dt({
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
G([z({ attribute: !1 })], Q.prototype, "hass", void 0), G([z({ attribute: !1 })], Q.prototype, "pending", void 0), G([z({ attribute: !1 })], Q.prototype, "running", void 0), G([z({ type: Number })], Q.prototype, "now", void 0), G([z({ type: Boolean })], Q.prototype, "isAdmin", void 0), G([z({ type: Boolean })], Q.prototype, "narrow", void 0), Q = G([R("at-upcoming-table")], Q);
// src/ha-elements.ts
var gt = [
	"hass-subpage",
	"ha-card",
	"ha-data-table",
	"ha-button",
	"ha-icon-button",
	"ha-dropdown",
	"ha-dropdown-item",
	"ha-svg-icon",
	"ha-filter-chip"
];
async function _t(e, t, n) {
	let r, i = new Promise((e) => r = setTimeout(e, n));
	return await Promise.race([Promise.all(t.map((t) => e.whenDefined(t).catch(() => void 0))), i]), clearTimeout(r), t.filter((t) => !e.get(t));
}
async function vt() {
	let e = document.createElement("partial-panel-resolver"), t = { config: {
		component_name: "config",
		url_path: "config"
	} };
	e.hass = { panels: t }, await e._getRoutes(t).routes.config.load(), await customElements.whenDefined("ha-panel-config"), await document.createElement("ha-panel-config").routerOptions.routes.automation.load();
}
async function yt(e, t, n, r) {
	let i = Date.now() + r;
	if (n.some((t) => !e.get(t))) {
		let e, n = new Promise((t) => e = setTimeout(t, r)), i = t().catch((e) => {
			console.warn("Scheduled Jobs: could not load Home Assistant's panel elements", e);
		});
		await Promise.race([i, n]), clearTimeout(e);
	}
	let a = await _t(e, n, Math.max(0, i - Date.now()));
	return a.length && console.warn("Scheduled Jobs: Home Assistant elements missing:", a.join(", ")), a;
}
var bt;
function xt(e = 1e4) {
	return bt ??= yt(customElements, vt, gt, e), bt;
}
// src/reconnect.ts
var St = 1e3, Ct = 3e4;
function wt(e) {
	return Math.min(St * 2 ** Math.min(e, 10), Ct);
}
// src/at-panel.ts
var Tt = "Scheduled Jobs", $ = class extends L {
	constructor(...e) {
		super(...e), this.narrow = !1, this.data = {
			pending: [],
			running: [],
			history: []
		}, this.now = Date.now(), this.reconnecting = !0, this.error = "", this.confirmCancelAll = !1, this.addOpen = !1, this.attempt = 0, this.subscribed = !1, this.gone = !1, this.generation = 0, this.onRun = (e) => {
			let t = this.hass;
			t && this.call(() => ze(t, e.detail.job.id));
		}, this.onCancel = (e) => {
			let t = this.hass;
			t && this.call(() => Re(t, [e.detail.job.id]));
		}, this.onReschedule = (e) => {
			let t = this.hass;
			t && this.call(() => Be(t, e.detail.job.id, e.detail.due));
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
		this.hass && !this.subscribed && (this.subscribed = !0, He(this.hass).then((e) => this.atInfo = e, () => void 0), xt().then((e) => this.missing = e), await this.subscribe());
	}
	async subscribe() {
		if (!this.hass || this.gone) return;
		let e = this.generation;
		try {
			let t = await Fe(this.hass, (t) => {
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
		if ("snapshot" in e) this.data = lt(e.snapshot), this.reconnecting = !1, this.attempt = 0;
		else if ("change" in e) this.data = ut(this.data, e.change);
		else if ("stopped" in e) {
			let e = this.unsub;
			this.unsub = void 0, e?.().catch(() => void 0), this.scheduleRetry();
		}
	}
	scheduleRetry() {
		if (this.reconnecting = !0, this.gone) return;
		let e = wt(this.attempt++);
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
		this.confirmCancelAll = !1;
		let t = this.data.pending.map((e) => e.id);
		t.length && this.call(() => Re(e, t));
	}
	clearHistory() {
		let e = this.hass;
		this.confirmCancelAll = !1, e && this.call(() => Ve(e));
	}
	onMenuSelect(e) {
		let t = e.detail.item.value;
		t === "cancel-all" ? (this.confirmCancelAll || e.preventDefault(), this.cancelAll()) : t === "clear-history" && this.clearHistory();
	}
	get title_() {
		let e = this.panel?.config?.title;
		return typeof e == "string" && e ? e : Tt;
	}
	render() {
		if (this.missing === void 0) return A;
		if (this.missing.length) return O`<div class="missing">
        <p>This panel needs an update for this Home Assistant version.</p>
        <p>Missing: ${this.missing.join(", ")}</p>
      </div>`;
		let e = this.atInfo?.is_admin ?? !1;
		return O`
      <hass-subpage main-page .hass=${this.hass} .narrow=${this.narrow} .header=${this.title_}>
        <ha-dropdown
          slot="toolbar-icon"
          placement="bottom-end"
          @wa-select=${this.onMenuSelect}
          @wa-after-hide=${() => this.confirmCancelAll = !1}
        >
          <ha-icon-button slot="trigger" .label=${"More options"} .path=${"M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z"}></ha-icon-button>
          <ha-dropdown-item value="cancel-all">${this.confirmCancelAll ? "Confirm cancel all?" : "Cancel all"}</ha-dropdown-item>
          <ha-dropdown-item value="clear-history">Clear history</ha-dropdown-item>
        </ha-dropdown>
        <div class="content" @run-job=${this.onRun} @cancel-job=${this.onCancel} @reschedule-job=${this.onReschedule} @open-job=${this.onOpen}>
          ${this.reconnecting ? O`<div class="notice">Reconnecting…</div>` : A}
          ${this.error ? O`<div class="error" role="alert">${this.error}<button aria-label="Dismiss" @click=${() => this.error = ""}>✕</button></div>` : A}
          <at-upcoming-table
            .hass=${this.hass}
            .pending=${this.data.pending}
            .running=${this.data.running}
            .now=${this.now}
            .isAdmin=${e}
            .narrow=${this.narrow}
          ></at-upcoming-table>
          <at-history-table .hass=${this.hass} .history=${this.data.history} .now=${this.now} .narrow=${this.narrow}></at-history-table>
        </div>
        <ha-button slot="fab" size="l" @click=${() => this.addOpen = !0}>
          <ha-svg-icon slot="start" .path=${"M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"}></ha-svg-icon>
          Add job
        </ha-button>
      </hass-subpage>
      <at-add-job-dialog .hass=${this.hass} .isAdmin=${e} .open=${this.addOpen} @close-add-job=${() => this.addOpen = !1}></at-add-job-dialog>
      <at-job-details .hass=${this.hass} .job=${this.details} @close-details=${() => this.details = void 0}></at-job-details>
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
G([z({ attribute: !1 })], $.prototype, "hass", void 0), G([z({ type: Boolean })], $.prototype, "narrow", void 0), G([z({ attribute: !1 })], $.prototype, "panel", void 0), G([z({ attribute: !1 })], $.prototype, "route", void 0), G([B()], $.prototype, "missing", void 0), G([B()], $.prototype, "data", void 0), G([B()], $.prototype, "now", void 0), G([B()], $.prototype, "reconnecting", void 0), G([B()], $.prototype, "error", void 0), G([B()], $.prototype, "confirmCancelAll", void 0), G([B()], $.prototype, "details", void 0), G([B()], $.prototype, "atInfo", void 0), G([B()], $.prototype, "addOpen", void 0), $ = G([R("at-panel")], $);
export { $ as AtPanel };
