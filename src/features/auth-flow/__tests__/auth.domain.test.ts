import { describe, it, expect } from "vitest";
import { 
    validarDNI, 
    esIdentificadorValido, 
    esPasswordFuerte, 
    validarCredencialesLogin,
    validarOTP,
    generarOTP,
    crearJWTClamasFake,
    decodificarJWTClaims
} from "../domain/auth.domain";

describe("RN-AUT-01: validarDNI (ya implementada)", () => {
    it("Debe devolver true para NIF español válido con letra correcta", () => {
        // 12345678 % 23 = Z
        expect(validarDNI("12345678Z")).toBe(true);
    });
    it("Debe devolver false con letra de control incorrecta", () => {
        expect(validarDNI("12345678B")).toBe(false);
    });
    it("Debe rechazar DNI con menos de 8 dígitos", () => {
        expect(validarDNI("1234567A")).toBe(false);
    });
    it("Debe rechazuar DNI con más de 8 dígitos", () => {
        expect(validarDNI("123456789A")).toBe(false);
    });
});

describe("RN-AUT-01: esIdentificadorValido (ya implementada)", () => {
    it("Debe aceptar formato pasaporte X + 7 dígitos + letra", () => {
        expect(esIdentificadorValido("X1234567A")).toBe(true);
    });
    it("Debería dar false para identificador vacío", () => {
        expect(esIdentificadorValido("")).toBe(false);
    });
});

describe("RN-AUT-03: esPassword Fuerte (función nueva)", () => {
    it("Debe devolver false para contraseña vacía", () => {
        expect(esPasswordFuerte("")).toBe(false);
    });
    it("Debería devolver false para null/undefined", () => {
        expect(esPasswordFuerte(null as any)).toBe(false);
    });
    it("Debe retornar false si < 8 caracteres (RN-AUT-03)", () => {
        expect(esPasswordFuerte("Aa1bc")).toBe(false);
    });
});

describe("RN-AUT-02: validarCredencialesLogin", () => {
    it("Debe devolver false para NIF inválido con contraseña fuerte", () => {
        const r = validarCredencialesLogin("ZZZ98765", "Aa1bcdef");
        expect(r.valid).toBe(false);
        expect(r.error).toContain("NIF/Pasaporte incorrecto");
    });
    it("Debe devolver false para NIF válido pero contraseña débil (sin dígito)", () => {
        const r = validarCredencialesLogin("12345678Z", "Abcdefgh");
        expect(r.valid).toBe(false);
    });
    it("Deberia devolver true para NIF válido y contraseña fuerte (RN-AUT-01 + RN-AUT-03)", () => {
        const r = validarCredencialesLogin("12345678Z", "Aa1bcdef");
        expect(r.valid).toBe(true);
        expect(r.error).toBeNull();
    });
});

describe("RN-AUT-04: validarOTP", () => {
    it("Debe devolver true para OTP de 6 dígitos válidos", () => {
        expect(validarOTP("123456")).toBe(true);
        expect(validarOTP("000000")).toBe(true);
        expect(validarOTP("999999")).toBe(true);
    });
    it("Debe devolver false para OTP con menos de 6 dígitos", () => {
        expect(validarOTP("12345")).toBe(false);
    });

});

describe("RN-AUT-04: generarOTP", () => {
    it("Deberia devolver una cadena de exactamente 6 digitos", () => {
        const otp = generarOTP();
        expect(otp).toHaveLength(6);
        expect(validarOTP(otp)).toBe(true);
    });
});

describe("RN-AUT-05: JWT functions", () => {
    it("Debe crear un token con separador . y devolver claims originales al decodificarlo", () => {
        const CLAIMS = { sub: "AlumnoId123", roles: ["student"], exp: 946684800, iat: 946684740 };
        const token = crearJWTClamasFake(CLAIMS);
        expect(token).toContain(".");
        const decoded = decodificarJWTClaims(token);
        expect(decoded).not.toBeNull();
        if (decoded) {
            expect((decoded as any).sub).toBe("AlumnoId123");
        }
    });
});
