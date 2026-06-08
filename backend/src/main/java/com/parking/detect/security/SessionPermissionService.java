package com.parking.detect.security;

import com.parking.detect.entity.SysUser;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.Arrays;

@Service
public class SessionPermissionService {

    public SysUser requireLogin(HttpSession session) {
        Object currentUser = session.getAttribute("currentUser");
        if (currentUser instanceof SysUser user) {
            return user;
        }
        throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "请先登录后再操作");
    }

    public SysUser requireAnyRole(HttpSession session, String... roles) {
        SysUser user = requireLogin(session);
        if (roles == null || roles.length == 0) {
            return user;
        }

        String currentRole = normalizeRole(user.getRole());
        boolean matched = Arrays.stream(roles)
                .map(this::normalizeRole)
                .anyMatch(currentRole::equals);

        if (!matched) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "当前账号无权限执行该操作");
        }
        return user;
    }

    private String normalizeRole(String role) {
        return role == null ? "" : role.trim().toUpperCase();
    }
}
