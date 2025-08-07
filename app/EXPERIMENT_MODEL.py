# %% [markdown]
# # Import libraries

# %%
import numpy as np
import scipy.integrate
from scipy import signal
from scipy.optimize import newton
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import CoolProp.CoolProp as Clp

np.set_printoptions(threshold=np.inf) # print all variable to the screen

# %% [markdown]
# # Data

# %%
# Load the data from the text file
data = pd.read_csv('Datos_laboratorio.txt', delimiter='\t')
columns = ['F2[m^3/s]', 'F7[m^3/s]', 'F8[m^3/s]', 'F9[m^3/s]']

eps = np.finfo(float).eps # [-] ------ Value of machine precision
# Replaces values less than 0 with eps in the specified columns
data[columns] = data[columns].mask(data[columns] < 0, eps)about:blank#blocked

# %% [markdown]
# # Geometry of the reactor and heat exchanger

# %%
class Reactor_geometry:
    """
    ==========================
    class Reactor_geometry
    ==========================
    Description: contains the different geometric data of the reactor and
                 the jacket.
    """
    # Reactor dimensions
    lcr = 0.28
    rwall_thickness = 0.0007
    d_i_r = 0.1648
    d_e_r = d_i_r + 2*rwall_thickness
    Across_r = (np.pi * (d_i_r**2)) / 4
    rbtawj = (np.pi * (d_e_r**2)) / 4

    # Jacket dimensions
    d_j = 0.18
    d_j_i = d_e_r
    jwall_thickness = rwall_thickness
    d_j_e = d_j - 2*jwall_thickness
    r_j_i = d_j_i/2
    r_j_e = d_j_e/2
    j_thickness = r_j_e - r_j_i

R_geo = Reactor_geometry()

# %% [markdown]
# # Correlations data

# %%
class Reactor_correlation_parameters:
    """
    =======================================
    class Reactor_correlation_parameters
    =======================================
    """
    # Heat transfer coefficient in the reactor
    k_I = 0.4
    k_I_II = 1.2
    k_I_inf = 1.2
    A = 0.46
    d_a = 0.11
    # Heat transfer coefficient in the jacket
    k_II_inf = 1.2
    E = 0.8
    d_g = (8/3)**0.5 * R_geo.j_thickness
    do = 0.005
    P_II = 101325

Rc_param = Reactor_correlation_parameters()

# %% [markdown]
# # Physical parameters

# %%
class parameters:
    """
    ===================
    class parameters
    ===================
    """
    # Temperatures
    T_ref = 273.15
    T_inf = 273.15 + 23
    T7 = T_inf
    T8 = T_inf
    T9 = T_inf
    # Average properties
    T2_mean = data['T2[K]'].mean()
    T3_mean = data['T3[K]'].mean()
    # Parameters simulation
    eps = np.finfo(float).eps
    win = signal.windows.hann(60)
    tol = 1.0e-5
    max_iter = 200
    g = 9.81
    F2_min = 7.35e-5
    t_rec = 1303
    # Jacket
    Ro_2 = Clp.PropsSI('D', 'T', T2_mean, 'P', Rc_param.P_II, 'H2O')
    Ro_3 = Clp.PropsSI('D', 'T', T3_mean, 'P', Rc_param.P_II, 'H2O')
    Cp_2 = Clp.PropsSI('C', 'T', T2_mean, 'P', Rc_param.P_II, 'H2O')
    Cp_3 = Clp.PropsSI('C', 'T', T3_mean, 'P', Rc_param.P_II, 'H2O')
    # Cooling jacket resistance
    Tm_II = (T2_mean + T3_mean) / 2
    rho_II = Clp.PropsSI('D', 'T', Tm_II, 'P', Rc_param.P_II, 'H2O')
    mu_II = Clp.PropsSI('V', 'T', Tm_II, 'P', Rc_param.P_II, 'H2O')
    beta_II = Clp.PropsSI('ISOBARIC_EXPANSION_COEFFICIENT', 'T', Tm_II, 'P', Rc_param.P_II, 'H2O')
    # Prandlt number jacket
    k_II = Clp.PropsSI('L', 'T', Tm_II, 'P', Rc_param.P_II, 'H2O')
    Cp_II = Clp.PropsSI('C', 'T', Tm_II, 'P', Rc_param.P_II, 'H2O')
    Pr_II = mu_II * Cp_II / k_II
    # Stream densities
    Rho_I = 1056.688211
    Rho_7 = 943.73
    Rho_8 = 1008.93
    Rho_9 = 988.92
    # Specific heats
    Cp_I = 1720*0.85
    Cp_7 = 1566
    Cp_8 = 3576
    Cp_9 = 3654
    # Reaction enthalpies
    DeltaH_VAM = -8.96e7
    DeltaH_BA = -7.54e7
    # Viscosity parameters
    a0 = 555.556
    c0 = 0.0001
    c1 = 14.3
    c2 = 15.45
    c3 = 1.563

param = parameters()

# %% [markdown]
# # Data storage lists

# %%
class lts:
    """
    ============
    class lts
    ============
    """
    tt_ = []
    Q1 = []
    U1 = []

lists = lts()

# %% [markdown]
# # Calculation of initial volume and initial concentrations of the reactor

# %%
class initial_reactor:
    """
    ========================
    class initial_reactor
    ========================
    """
    CNaPS_8 = 0.167
    CTBHP_8 = 0.111
    CCRD_9 = 0.131
    Cs = 0.034
    P_ = 101325
    T_ = param.T_inf
    Ro_water = Clp.PropsSI('D', 'T', T_, 'P', P_, 'H2O')
    MwCRD = 176.12
    MwNaPS = 82.03
    MwTBHP = 90.12
    MWater_0ri = 0.53479
    MWater_COXi0 = 0.02577
    MWater_CDRi0 = 0.01266
    MWater_0r = MWater_0ri + MWater_COXi0 + MWater_CDRi0
    MCRD_r0 = 0.00066
    MNaPS_r0 = 0.0007
    MTBHP_r0 = 0.00042
    VWater_r0 = MWater_0r / Ro_water
    V_0r = VWater_r0
    CCRD_r0i = MCRD_r0 / MwCRD / V_0r
    CNaPS_r0i = MNaPS_r0 / MwNaPS / V_0r
    CTBHP_r0i = MTBHP_r0 / MwTBHP / V_0r

init_R = initial_reactor()

# %% [markdown]
# # Data for reaction rates

# %%
class param_rates:
    """
    ====================
    class param_rates
    ====================
    """
    NA = 6.022e23
    Rg = 8.31446e-3
    nbarr = 0.5
    # Molecular weight
    Mw_VAM = 86.09
    Mw_BA = 128.18
    # Acentric factors
    A_VAM = 6.14e7
    A_BA = 2.73e7
    A_redox = 11649.28
    A_thermal = 2.57E+17
    # Activation energy
    E_redox = 32.19
    E_pol = 3171
    E_ther = 16720
    # Reactivity radius
    r1 = 0.037
    r2 = 6.35
    # Mole fraction of monomer
    CVAM_7 = 5.577
    CBA_7 = 1.93
    f1 = CVAM_7 / (CVAM_7 + CBA_7)
    f2 = 1 - f1

r_param = param_rates()

# %% [markdown]
# # Laboratory process class

# %%
class Laboratory_process:
    def __init__(self, t_add, Adj_factor, data):
        self.t_add = t_add
        self.f_j1 = Adj_factor[0]
        self.f_j2 = Adj_factor[1]
        self.data = data
        self.t_Laboratory = data['t[s]'].values
        self.T1_Laboratory = data['T1[K]'].values
        self.T3_Laboratory = data['T3[K]'].values

        # Suavizar y crear funciones de interpolación para los datos de entrada
        F2_smooth = signal.convolve(data['F2[m^3/s]'], param.win, mode='same') / sum(param.win)
        F7_smooth = signal.convolve(data['F7[m^3/s]'], param.win, mode='same') / sum(param.win)
        F8_smooth = signal.convolve(data['F8[m^3/s]'], param.win, mode='same') / sum(param.win)
        F9_smooth = signal.convolve(data['F9[m^3/s]'], param.win, mode='same') / sum(param.win)
        RPS_smooth = signal.convolve(data['RPS[RPS]'], param.win, mode='same') / sum(param.win)
        T2_smooth = signal.convolve(data['T2[K]'], param.win, mode='same') / sum(param.win)

        # Crear funciones de interpolación
        self.F2_func = interp1d(self.t_Laboratory, F2_smooth, bounds_error=False, fill_value="extrapolate")
        self.F7_func = interp1d(self.t_Laboratory, F7_smooth, bounds_error=False, fill_value="extrapolate")
        self.F8_func = interp1d(self.t_Laboratory, F8_smooth, bounds_error=False, fill_value="extrapolate")
        self.F9_func = interp1d(self.t_Laboratory, F9_smooth, bounds_error=False, fill_value="extrapolate")
        self.RPS_func = interp1d(self.t_Laboratory, RPS_smooth, bounds_error=False, fill_value="extrapolate")
        self.T2_func = interp1d(self.t_Laboratory, T2_smooth, bounds_error=False, fill_value="extrapolate")

    def feed_tank_Ci(self, t):
        # Usar np.where para manejar tanto un número (float) como un array para t
        CVAM_7 = np.where(t < self.t_add, 5.577, 5.047)
        CBA_7 = np.where(t < self.t_add, 1.93, 1.75)
        CNaPS_8 = np.where(t < self.t_add, 0.167, 0.143)
        CTBHP_8 = np.where(t < self.t_add, 0.111, 0.135)
        return CVAM_7, CBA_7, CNaPS_8, CTBHP_8

    def reaction_kinetics(self, T, CVAM_7, CBA_7, CVAM_1, CBA_1, CTBHP_1, CNaPS_1, CCRD_1, Np):
        f1 = CVAM_7 / (CVAM_7 + CBA_7)
        f2 = 1 - f1
        kp11 = r_param.A_VAM * np.exp(-r_param.E_pol / T)
        kp22 = r_param.A_BA * np.exp(-r_param.E_pol / T)
        kp21 = kp22 / r_param.r2
        kp12 = kp11 / r_param.r1
        phi1 = (kp21 * f1) / (kp21 * f1 + kp12 * f2)
        phi2 = 1 - phi1
        kp1 = (kp11 * phi1) + (kp21 * phi2)
        kp2 = (kp12 * phi1) + (kp22 * phi2)
        R_VAM = (Np * r_param.nbarr * kp1 * CVAM_1 / r_param.NA) * 1e3
        R_BA = (Np * r_param.nbarr * kp2 * CBA_1 / r_param.NA) * 1e3
        k_redox = r_param.A_redox * np.exp(-r_param.E_redox / (T * r_param.Rg))
        R_redox = k_redox * CCRD_1 * CTBHP_1
        k_thermal = r_param.A_thermal * np.exp(-r_param.E_ther / T)
        R_thermal = k_thermal * CNaPS_1
        return R_VAM, R_BA, R_redox, R_thermal

    def mu_POL(self, T, CMPOL):
        mu = param.c0 * np.exp(param.c1 * CMPOL / param.Rho_I) * 10**(param.c2 * ((param.a0 / T) - param.c3))
        return mu

    def Nusselt_number_reactor(self, RPS, CMPOL_1, T1):
        mu_I = self.mu_POL(T1, CMPOL_1)
        Re_I = RPS * Rc_param.d_a**2 * param.Rho_I / mu_I
        Pr_I = mu_I * param.Cp_I / Rc_param.k_I
        mu_w_I = mu_I * 1.05
        Nu_I = Rc_param.A * Re_I**(2/3) * Pr_I**(1/3) * (mu_I / mu_w_I)**0.14
        return Nu_I

    def Nusselt_number_jacket_forced(self, L_II, mu_II, rho_II, Pr_II, F3):
        d_g = (8/3)**0.5 * R_geo.j_thickness
        mu_iw_II = mu_II * 1.05
        uO = F3 / (np.pi / 4 * Rc_param.do**2)
        uS = F3 / (L_II * R_geo.j_thickness)
        u_II = (uS * uO)**0.5
        Re_II = rho_II * u_II * d_g / mu_II
        Nu_II_forced = 0.03 * Re_II**0.75 * Pr_II / (1 + 1.74 * (Pr_II - 1) / Re_II**0.125) * (mu_II / mu_iw_II)**0.14
        return Nu_II_forced

    def Rayleigh_number(self, Lc, T, Tw, rho, mu, Pr, beta):
        mu_kinematic = mu / rho
        Delta_T = abs(Tw - T)
        Gr = param.g * beta * Delta_T * Lc**3 / mu_kinematic**2
        Ra = Gr * Pr
        return Ra

    def Nusselt_number_jacket_natural(self, L_II, Ra_II):
        N = (Ra_II * (L_II / R_geo.j_thickness)**3)**(-0.25) * (L_II / R_geo.r_j_i)
        if N <= 0.2:
            C1, C2, n1, n2 = [0.48, 854, 0.75, 0]
        elif 0.2 < N < 1.48:
            C1, C2, n1, n2 = [0.93, 1646, 0.84, 0.36]
        else:
            C1, C2, n1, n2 = [0.49, 862, 0.95, 0.8]
        Nu_II_free = (C1 * Ra_II * (L_II / R_geo.j_thickness)**2 / (C2 * (L_II / R_geo.r_j_e)**4 * (R_geo.r_j_e / L_II) + (Ra_II * (L_II / R_geo.j_thickness)**3)**n1 * (R_geo.r_j_i / L_II)**n2))
        return Nu_II_free

    def jacket_objective_function(self, T_IIi, *args):
        L_II, A_IIi, T1, T4, rho_II, mu_II, k_II, Pr_II, beta_II, R_fiII, R_I, R_fiI, Rw_I_II = args
        Ra_II = self.Rayleigh_number(R_geo.j_thickness, T4, T_IIi, rho_II, mu_II, Pr_II, beta_II)
        Nu_II = self.Nusselt_number_jacket_natural(L_II, Ra_II)
        h_II = Nu_II * k_II / R_geo.j_thickness
        R_II = 1 / (h_II * A_IIi)
        obj = (R_fiII + R_II) / (R_I + R_fiI + Rw_I_II) * (T1 - T_IIi) + T4 - T_IIi
        return obj

    def AU_RJ(self, t, L, A_Ii, A_IIi, A_IIe, A_IIo, CMPOL_1, T1, T3):
        F2 = self.F2_func(t)
        F3 = F2
        RPS = self.RPS_func(t)

        Nu_I = self.Nusselt_number_reactor(RPS, CMPOL_1, T1)
        h_I = Nu_I * Rc_param.k_I / R_geo.d_i_r
        R_I = 1 / (h_I * A_Ii)
        R_fiI = 0.0005 / A_Ii
        Rw_I_II = np.log(R_geo.d_e_r / R_geo.d_i_r ) / (2*np.pi * L * Rc_param.k_I_II)
        R_fiII = 0.0002 / A_IIi

        if F3 < param.F2_min:
            try:
                T_IIi_initial = T1 - 0.5
                T_IIi = newton(self.jacket_objective_function, T_IIi_initial, args=(L, A_IIi, T1, T3, param.rho_II, param.mu_II, param.k_II, param.Pr_II, param.beta_II, R_fiII, R_I, R_fiI, Rw_I_II), tol=param.tol, maxiter=param.max_iter)
            except RuntimeError:
                T_IIi = (T1 + T3) / 2
            Ra_II = self.Rayleigh_number(R_geo.j_thickness, T3, T_IIi, param.rho_II, param.mu_II, param.Pr_II, param.beta_II)
            Nu_II = self.Nusselt_number_jacket_natural(L, Ra_II)
            h_II = Nu_II * param.k_II / R_geo.j_thickness
            R_II = 1 / (h_II * A_IIi)
            AU_I = 1 / (R_I + R_fiI + Rw_I_II + R_fiII + R_II) * self.f_j1
        else:
            Nu_II = self.Nusselt_number_jacket_forced(L, param.mu_II, param.rho_II, param.Pr_II, F3)
            h_II = Nu_II * param.k_II / Rc_param.d_g
            R_II = 1 / (h_II * A_IIi)
            AU_I = 1 / (R_I + R_fiI + Rw_I_II + R_fiII + R_II) * self.f_j2

        R_I_ = 1 / (h_I * R_geo.Across_r)
        R_fiI_ = 0.0005 / R_geo.Across_r
        Rw_I_inf = R_geo.jwall_thickness / (R_geo.rbtawj * Rc_param.k_I_inf)
        h_I_inf = 20
        R_I_inf = 1 / (h_I_inf * R_geo.Across_r)
        AU_Il = 1 / (R_I_ + R_fiI_ + Rw_I_inf + R_I_inf)

        R_foII = 0.0002 / A_IIo
        Rw_II_inf = np.log(R_geo.d_j / R_geo.d_j_e) / (2*np.pi * L * Rc_param.k_II_inf)
        h_II_inf = 20
        R_II_inf = 1 / (h_II_inf * A_IIe)
        AU_IIl = 1 / (R_II + R_foII + Rw_II_inf + R_II_inf)
        return AU_I, AU_Il, AU_IIl

    def Reactor(self, t, y):
        L, CVAM_1, CBA_1, CNaPS_1, CTBHP_1, CCRD_1, CMPOL_1, Np_I, T1, T3 = y

        F7 = self.F7_func(t)
        F8 = self.F8_func(t)
        F9 = self.F9_func(t)
        T2 = self.T2_func(t)
        F2 = self.F2_func(t)
        F3 = F2

        V_I = R_geo.Across_r * L
        A_Ii = np.pi * L * R_geo.d_i_r + R_geo.rbtawj
        A_IIi = np.pi * L * R_geo.d_j_i + R_geo.rbtawj
        A_IIo = np.pi * L * R_geo.d_j_e + R_geo.rbtawj
        A_IIe = np.pi * L * R_geo.d_j + R_geo.rbtawj

        CVAM_7, CBA_7, CNaPS_8, CTBHP_8 = self.feed_tank_Ci(t)
        R_VAM_I, R_BA_I, R_redox_I, R_thermal_I = self.reaction_kinetics(T1, CVAM_7, CBA_7, CVAM_1, CBA_1, CTBHP_1, CNaPS_1, CCRD_1, Np_I)

        dLdt = (F7 + F8 + F9) / R_geo.Across_r
        V_I = max(V_I, param.eps)

        if t < param.t_rec:
            dNp_Idt = (R_redox_I + 2 * R_thermal_I) * V_I * r_param.NA * 1e3
        else:
            dNp_Idt = 0
        dCNaPS_1dt = (F8 * init_R.CNaPS_8 / V_I) - R_thermal_I - (CNaPS_1 * R_geo.Across_r * dLdt / V_I)
        dCTBHP_1dt = (F8 * init_R.CTBHP_8 / V_I) - R_redox_I - (CTBHP_1 * R_geo.Across_r * dLdt / V_I)
        dCCRD_1dt = (F9 * init_R.CCRD_9 / V_I) - R_redox_I - (CCRD_1 * R_geo.Across_r * dLdt / V_I)
        dCVAM_1dt = (F7 * CVAM_7 / V_I) - (R_VAM_I / V_I) - (CVAM_1 * R_geo.Across_r * dLdt / V_I)
        dCBA_1dt = (F7 * CBA_7 / V_I) - (R_BA_I / V_I) - (CBA_1 * R_geo.Across_r * dLdt / V_I)
        dCMPOL_1dt = (R_VAM_I * r_param.Mw_VAM / V_I) + (R_BA_I * r_param.Mw_BA / V_I) - (CMPOL_1 * R_geo.Across_r * dLdt / V_I)
        
        AU_I, AU_Il, AU_IIl = self.AU_RJ(t, L, A_Ii, A_IIi, A_IIe, A_IIo, CMPOL_1, T1, T3)
        
        Q_I = AU_I * (T1 - T3)
        Q_Il = AU_Il * (T1 - param.T_inf)

        dT1dt = (1 / (param.Cp_I * param.Rho_I * V_I)) * (
            param.Cp_7 * F7 * param.Rho_7 * (param.T7 - T1) +
            param.Cp_8 * F8 * param.Rho_8 * (param.T8 - T1) +
            param.Cp_9 * F9 * param.Rho_9 * (param.T9 - T1) -
            R_VAM_I * param.DeltaH_VAM - R_BA_I * param.DeltaH_BA -
            Q_I - Q_Il)

        V_II = np.pi * L * (R_geo.d_j_e**2 - R_geo.d_j_i**2) / 4
        V_II = max(V_II, param.eps)
        Q_IIl = AU_IIl * (T3 - param.T_inf)
        dT3dt = (1 / (param.Ro_3 * param.Cp_3 * V_II)) * (
            F2 * param.Ro_2 * param.Cp_2 * (T2 - T3) + Q_I - Q_IIl)
        
        lists.tt_.append(t)
        lists.Q1.append(Q_I)
        lists.U1.append(AU_I)
        
        return [dLdt, dCVAM_1dt, dCBA_1dt, dCNaPS_1dt, dCTBHP_1dt, dCCRD_1dt, dCMPOL_1dt, dNp_Idt, dT1dt, dT3dt]

    def Reactor_solver(self, t_span, dt, y_0):
        print('===> Simulation has started.')
        t_eval = np.arange(t_span[0], t_span[1], dt)
        
        sol = scipy.integrate.solve_ivp(
            fun=self.Reactor,
            t_span=t_span,
            y0=y_0,
            method='BDF',
            t_eval=t_eval,
            dense_output=True
        )
        
        print('===> Simulation is over.')
        if sol.success:
            print(f'===> Solver finished successfully: {sol.message}')
            print('===> plotting ....')
            return sol.t, sol.y.T
        else:
            print(f'===> Solver failed: {sol.message}')
            return None, None

    def plotting(self, t, sol, theo, exp):
        if t is None or sol is None:
            print("No solution to plot.")
            return

        t_theo, C_theo = theo
        t_exp, C_exp, mu_exp = exp
        mu_exp1, mu_exp2, mu_exp3 = mu_exp

        L = sol[:,0]
        CVAM_1 = sol[:,1]
        CBA_1 = sol[:,2]
        CNaPS_1 = sol[:,3]
        CTBHP_1 = sol[:,4]
        CCRD_1 = sol[:,5]
        CMPOL_1 = sol[:,6]
        Np_I = sol[:,7]
        T1 = sol[:,8]
        T3 = sol[:,9]

        mu_I = self.mu_POL(T1, CMPOL_1)

        # Gráficos con Plotly
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=t, y=T1-273.15, mode='lines', name='T1 Simulación'))
        fig1.add_trace(go.Scatter(x=self.t_Laboratory, y=self.T1_Laboratory-273.15, mode='lines', name='T1 Laboratorio'))
        fig1.update_layout(title='Temperatura del Reactor T1 [°C] vs Tiempo [s]', xaxis_title='t [s]', yaxis_title='T1 [°C]', width=1150, height=500)
        fig1.show()

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=t, y=T3-273.15, mode='lines', name='T3 Simulación'))
        fig2.add_trace(go.Scatter(x=self.t_Laboratory, y=self.T3_Laboratory-273.15, mode='lines', name='T3 Laboratorio'))
        fig2.update_layout(title='Temperatura de la Chaqueta T3 [°C] vs Tiempo [s]', xaxis_title='t [s]', yaxis_title='T3 [°C]', width=1150, height=500)
        fig2.show()

        # Gráficos con Matplotlib
        fig5, ax = plt.subplots(4, 3, figsize=(15,18), constrained_layout=True)
        fig5.suptitle('Resultados de la Simulación del Reactor', fontsize=16)

        ax[0,0].plot(t, L, 'g')
        ax[0,0].set_xlabel(r'$t [s]$')
        ax[0,0].set_ylabel(r'$L[m]$')
        ax[0,0].set_title('Nivel del Reactor')
        ax[0,0].grid(True)
        
        ax[0,1].plot(t, CVAM_1)
        ax[0,1].set_xlabel(r'$t [s]$')
        ax[0,1].set_ylabel(r'$C[kmol/m^3]$')
        ax[0,1].set_title(r'Concentración $C_{VAM_r}$')
        ax[0,1].grid(True)

        ax[0,2].plot(t, CBA_1)
        ax[0,2].set_xlabel(r'$t [s]$')
        ax[0,2].set_ylabel(r'$C[kmol/m^3]$')
        ax[0,2].set_title(r'Concentración $C_{BA_r}$')
        ax[0,2].grid(True)
        
        ax[1,0].plot(t, CNaPS_1)
        ax[1,0].set_xlabel(r'$t [s]$')
        ax[1,0].set_ylabel(r'$C[kmol/m^3]$')
        ax[1,0].set_title(r'Concentración $C_{coxNaPS_r}$')
        ax[1,0].grid(True)
        
        ax[1,1].plot(t, CTBHP_1)
        ax[1,1].set_xlabel(r'$t [s]$')
        ax[1,1].set_ylabel(r'$C[kmol/m^3]$')
        ax[1,1].set_title(r'Concentración $C_{coxTBHP_r}$')
        ax[1,1].grid(True)
        
        ax[1,2].plot(t, CCRD_1)
        ax[1,2].set_xlabel(r'$t [s]$')
        ax[1,2].set_ylabel(r'$C[kmol/m^3]$')
        ax[1,2].set_title(r'Concentración $C_{CRD_r}$')
        ax[1,2].grid(True)

        ax[2,0].plot(t, CMPOL_1, label=r'$C_{MPOL_{sim}}$')
        ax[2,0].plot(t_theo, C_theo, 'o--', label=r'$C_{MPOL_{teórico}}$')
        ax[2,0].plot(t_exp, C_exp, 'x-', label=r'$C_{MPOL_{real}}$')
        ax[2,0].set_xlabel(r'$t [s]$')
        ax[2,0].set_ylabel(r'$C[kg/m^3]$')
        ax[2,0].set_title(r'Concentración de Polímero $C_{MPOL_r}$')
        ax[2,0].legend(); ax[2,0].grid(True)
        
        CVAM_7, CBA_7, _, _ = self.feed_tank_Ci(t)
        R_VAM_I, R_BA_I, _, _ = self.reaction_kinetics(T1, CVAM_7, CBA_7, CVAM_1, CBA_1, CTBHP_1, CNaPS_1, CCRD_1, Np_I)
        ax[2,1].plot(t, R_VAM_I, label=r'$R_{VAM_I}$')
        ax[2,1].plot(t, R_BA_I, label=r'$R_{BA_r}$')
        ax[2,1].set_xlabel(r'$t [s]$')
        ax[2,1].set_ylabel(r'$R[kmol/s]$')
        ax[2,1].set_title('Velocidades de Polimerización')
        ax[2,1].legend(); ax[2,1].grid(True)

        ax[2,2].plot(lists.tt_, lists.U1, 'r')
        ax[2,2].set_xlabel(r'$t [s]$')
        ax[2,2].set_ylabel(r'$U_j[W/K]$')
        ax[2,2].set_title('Coeficiente Global de Transferencia de Calor')
        ax[2,2].grid(True)

        ax[3,0].plot(lists.tt_, lists.Q1)
        ax[3,0].set_xlabel(r'$t [s]$')
        ax[3,0].set_ylabel(r'$\dot{Q_1}[W]$')
        ax[3,0].set_title('Tasa de Transferencia de Calor')
        ax[3,0].grid(True)

        _, _, R_redox_I, R_thermal_I = self.reaction_kinetics(T1, CVAM_7, CBA_7, CVAM_1, CBA_1, CTBHP_1, CNaPS_1, CCRD_1, Np_I)
        ax[3,1].plot(t, R_redox_I, label=r'$R_{redox_I}$')
        ax[3,1].plot(t, R_thermal_I, label=r'$R_{thermal_I}$')
        ax[3,1].set_xlabel(r'$t [s]$')
        ax[3,1].set_ylabel(r'$R[kmol/m^3/s]$')
        ax[3,1].set_title('Velocidades de Iniciación')
        ax[3,1].legend(); ax[3,1].grid(True)

        ax[3,2].plot(t, Np_I)
        ax[3,2].set_xlabel(r'$t [s]$')
        ax[3,2].set_ylabel(r'$N_p[-]$')
        ax[3,2].set_title('Número de Partículas de Polímero')
        ax[3,2].grid(True)

        plt.savefig('simulation_results.png', dpi=300, bbox_inches='tight')
        plt.show()

        # Viscosidad
        plt.figure(figsize=(10, 6))
        plt.plot(t, mu_I, label=r'$\mu_{simulada}$')
        plt.plot(t_exp, mu_exp1, 'o--', label=r'$\mu_{exp1}$')
        plt.plot(t_exp, mu_exp2, 's--', label=r'$\mu_{exp2}$')
        plt.plot(t_exp, mu_exp3, '^-', label=r'$\mu_{exp3}$')
        plt.xlabel(r'$t [s]$')
        plt.ylabel(r'$\mu_{mix_r}[Pa \cdot s]$')
        plt.title('Viscosidad del Polímero')
        plt.legend(); plt.grid(True)
        plt.savefig('viscosity_results.png', dpi=300, bbox_inches='tight')
        plt.show()

# %% [markdown]
# # Theoretical & Experimental data

# %%
t_theo = [0, 1200, 2700, 3600, 6300, 7200, 7380, 10800, 14340]
theo_porc = [0, 0.1227, 0.199, 0.3024, 0.4604, 0.4897, 0.4794, 0.5318, 0.5619]
C_theo = np.array(theo_porc) * param.Rho_I
theo = [t_theo, C_theo]

t_exp = [1200, 3600, 7200, 10800, 14340]
exp_porc = [0.1244, 0.3597, 0.4785, 0.5536, 0.5807]
C_exp= np.array(exp_porc) * param.Rho_I

mu_exp1 = [0, 0.006, 0.192, 0.714, 1.55]
mu_exp2 = [0, 0.008, 0.09, 0.432, 0.89]
mu_exp3 = [0.004, 0.008, 0.169, 0.86, 1.85]
mu_exp = [mu_exp1, mu_exp2, mu_exp3]

exp = [t_exp, C_exp, mu_exp]

# %% [markdown]
# # Execution times

# %%
t_add = 7380
t_process = 13970

# %% [markdown]
# # Initial conditions

# %%
L_0i = init_R.V_0r / R_geo.Across_r
CVAM_r0i = param.eps
CBA_r0i = param.eps
CCRD_r0i = init_R.CCRD_r0i
CMPOL_r0i = param.eps
CNaPS_r0i = init_R.CNaPS_r0i
CTBHP_r0i = init_R.CTBHP_r0i
Np_r0i = param.eps
T1_0i = data['T1[K]'].iloc[0]
T3_0i = data['T3[K]'].iloc[0]

y_0 = [L_0i, CVAM_r0i, CBA_r0i, CNaPS_r0i, CTBHP_r0i, CCRD_r0i, CMPOL_r0i, Np_r0i, T1_0i, T3_0i]

# %% [markdown]
# # Adjustment factors

# %%
f_j1 = 0.05
f_j2 = 10
Adj_factor = [f_j1, f_j2]

# %% [markdown]
# # ODE solver

# %%
Laboratory = Laboratory_process(t_add, Adj_factor, data)

t_0 = 0.0
t_span_end = 13100
dt = 1.0

# Simulación
t, sol = Laboratory.Reactor_solver(t_span=(t_0, t_span_end), dt=dt, y_0=y_0)

# Gráficos
if t is not None:
    Laboratory.plotting(t, sol, theo, exp)