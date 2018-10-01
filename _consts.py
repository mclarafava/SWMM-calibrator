from collections import OrderedDict

value_idx = 1
depth_idx = 0 # depth const used by swmm5 (python)
flow_idx = 4
minus_inf = -1000000000000000000000

_parameters_section_list = (
	'CN',
    'IMPERVIOUS',
    # 'N_PERV',
    # 'N_IMPERV',
    # 'S_PERV',
#    'S_IMPERV',
#    'PCT_ZERO',
    'ROUGHNESS'
)

# headers and lspace
subcatchments_header = OrderedDict()
subcatchments_header['subcatchment_id']=17
subcatchments_header['rain_gage']=17
subcatchments_header['outlet']=17
subcatchments_header['area']=9
subcatchments_header['imperv']=9
subcatchments_header['width']=10
subcatchments_header['slope']=10
subcatchments_header['curb_len']=9

subareas_header = OrderedDict()
subareas_header['subcatchment_id']=17
subareas_header['n_imperv']=11
subareas_header['n_perv']=11
subareas_header['s_imperv']=11
subareas_header['s_perv']=11
subareas_header['pct_zero']=11
subareas_header['route']=11
subareas_header['pct_route']=11

conduits_header = OrderedDict()
conduits_header ['conduit_id']=17
conduits_header ['from_node']=17
conduits_header ['to_node']=17
conduits_header ['length']=11
conduits_header ['roughness']=11
conduits_header ['in_offset']=11
conduits_header ['out_offset']=11
conduits_header ['init_flow']=11
conduits_header ['max_flow']=9

infiltration_header = OrderedDict()
infiltration_header['subcatchment_id']=17
infiltration_header['cn']=11
infiltration_header['hyd_con']=11
infiltration_header['dry_time']=9

transects_header = OrderedDict()
transects_header['nc']=12
transects_header['nLeft']=9
transects_header['nRight']=9
transects_header['nChannel']=9

headers = [subcatchments_header, subareas_header, conduits_header, infiltration_header, transects_header]
